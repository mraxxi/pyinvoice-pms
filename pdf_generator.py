# pdf_generator.py
"""
PDF generation functionality for the Invoice Generator application.
"""
import os
from typing import List
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

from models import Invoice, LineItem
import config
import utils


class PDFInvoiceGenerator:
    """Handles the generation of PDF invoices."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        # Create a custom title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.black
        )

        # Create a custom subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.black
        )

        # Create a custom normal style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.black
        )

        # Create a custom footer style
        self.footer_style = ParagraphStyle(
            'CustomFooter',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=1,  # Center alignment
            textColor=colors.grey,
            spaceAfter=6
        )

    def generate_pdf(self, invoice: Invoice, filename: str) -> bool:
        """
        Generate a PDF invoice and save it to the specified filename.
        Returns True if successful, False otherwise.
        """
        try:
            # Validate the invoice before generating PDF
            from models import InvoiceValidator
            errors = InvoiceValidator.validate_invoice(invoice)
            if errors:
                raise ValueError(f"Invalid invoice data: {', '.join(errors)}")

            # Create the PDF document
            doc = SimpleDocTemplate(
                filename,
                pagesize=config.PDF_PAGE_SIZE,
                rightMargin=config.PDF_MARGINS['right'],
                leftMargin=config.PDF_MARGINS['left'],
                topMargin=config.PDF_MARGINS['top'],
                bottomMargin=config.PDF_MARGINS['bottom']
            )

            # Build the content
            elements = self._build_pdf_content(invoice)

            # Generate the PDF
            doc.build(elements)
            return True

        except Exception as e:
            utils.log_error(f"Failed to generate PDF: {filename}", e)
            return False

    def _build_pdf_content(self, invoice: Invoice) -> List:
        """Build the content elements for the PDF."""
        elements = []

        # Add title
        elements.append(Paragraph("INVOICE", self.title_style))
        elements.append(Spacer(1, 5 * mm))

        # Add invoice header information
        elements.extend(self._build_header_section(invoice))
        elements.append(Spacer(1, 5 * mm))

        # Add customer information
        elements.extend(self._build_customer_section(invoice))
        elements.append(Spacer(1, 8 * mm))

        # Add line items table
        elements.append(self._build_items_table(invoice))
        elements.append(Spacer(1, 10 * mm))

        # Add footer
        elements.extend(self._build_footer_section())

        return elements

    def _build_header_section(self, invoice: Invoice) -> List:
        """Build the invoice header section."""
        elements = []

        elements.append(Paragraph(
            f"<b>Invoice #:</b> {invoice.invoice_number}",
            self.normal_style
        ))
        elements.append(Paragraph(
            f"<b>Date:</b> {invoice.invoice_date}",
            self.normal_style
        ))

        return elements

    def _build_customer_section(self, invoice: Invoice) -> List:
        """Build the customer information section."""
        elements = []

        elements.append(Paragraph("<b>Bill To:</b>", self.subtitle_style))
        elements.append(Paragraph(
            f"<b>{invoice.customer_name}</b>",
            self.normal_style
        ))
        elements.append(Paragraph(
            invoice.customer_address,
            self.normal_style
        ))

        return elements

    def _build_items_table(self, invoice: Invoice) -> Table:
        """Build the line items table."""
        # Prepare table data
        table_data = [
            ['#', 'Description', 'Qty', 'Price', 'Subtotal']
        ]

        # Add line items
        for item in invoice.line_items:
            table_data.append([
                str(item.number),
                item.description,
                str(item.amount),
                utils.format_currency(item.price),
                utils.format_currency(item.subtotal)
            ])

        # Add total row
        table_data.append([
            '',
            '',
            '',
            'Total:',
            f'{utils.format_currency(invoice.total)}'
        ])

        # Create table
        table = Table(table_data, colWidths=config.PDF_COLUMN_WIDTHS)

        # Apply table style
        table.setStyle(self._get_table_style(len(table_data)))

        return table

    def _get_table_style(self, num_rows: int) -> TableStyle:
        """Get the table style configuration."""
        style_commands = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, num_rows - 2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Number column
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Quantity column
            ('ALIGN', (3, 1), (4, -1), 'RIGHT'),  # Price and subtotal columns
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Total row styling
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('ALIGN', (3, -1), (4, -1), 'RIGHT'),

            # Grid and borders
            ('GRID', (0, 0), (-1, num_rows - 2), 0.5, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]

        return TableStyle(style_commands)

    def _build_footer_section(self) -> List:
        """Build the footer section."""
        elements = []

        elements.append(Paragraph(
            "Thank you for your business!",
            self.footer_style
        ))

        return elements


class PDFPreviewGenerator:
    """Handles PDF preview generation for display purposes."""

    @staticmethod
    def generate_preview_data(invoice: Invoice) -> dict:
        """
        Generate preview data that can be displayed in the UI.
        Returns a dictionary with formatted invoice data.
        """
        preview_data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date,
            'customer_name': invoice.customer_name,
            'customer_address': invoice.customer_address,
            'line_items': [],
            'total': utils.format_currency(invoice.total),
            'total_numeric': invoice.total
        }

        for item in invoice.line_items:
            preview_data['line_items'].append({
                'number': item.number,
                'description': item.description,
                'amount': item.amount,
                'price': utils.format_currency(item.price),
                'subtotal': utils.format_currency(item.subtotal),
                'price_numeric': item.price,
                'subtotal_numeric': item.subtotal
            })

        return preview_data


class PDFExportManager:
    """Manages PDF export operations including file handling."""

    def __init__(self):
        self.generator = PDFInvoiceGenerator()

    def export_invoice(self, invoice: Invoice, filename: str = None) -> tuple[bool, str]:
        """
        Export an invoice to PDF.
        Returns (success, message_or_error).
        """
        if not filename:
            filename = self._generate_default_filename(invoice)

        try:
            # Ensure the directory exists
            directory = os.path.dirname(filename)
            if directory and not utils.ensure_directory_exists(directory):
                return False, f"Cannot create directory: {directory}"

            # Generate the PDF
            success = self.generator.generate_pdf(invoice, filename)

            if success:
                return True, f"Invoice PDF saved to: {filename}"
            else:
                return False, "Failed to generate PDF"

        except Exception as e:
            utils.log_error(f"PDF export failed for {filename}", e)
            return False, f"Export failed: {str(e)}"

    def export_and_open(self, invoice: Invoice, filename: str = None) -> tuple[bool, str]:
        """
        Export an invoice to PDF and open it with the default application.
        Returns (success, message_or_error).
        """
        success, message = self.export_invoice(invoice, filename)

        if success:
            # Extract filename from the success message
            if "Invoice PDF saved to: " in message:
                saved_filename = message.replace("Invoice PDF saved to: ", "")
                if utils.open_file_with_default_app(saved_filename):
                    return True, f"{message}\nOpened with default application."
                else:
                    return True, f"{message}\nCould not open automatically."

        return success, message

    def _generate_default_filename(self, invoice: Invoice) -> str:
        """Generate a default filename for the invoice PDF."""
        safe_number = utils.get_safe_filename(invoice.invoice_number)
        filename = f"Invoice_{safe_number}.pdf"

        # Try to save in user's Documents folder
        suggested_path = utils.FileManager.suggest_save_location(filename)
        return suggested_path


class PDFValidationError(Exception):
    """Exception raised when PDF generation fails due to validation errors."""
    pass


class PDFGenerationError(Exception):
    """Exception raised when PDF generation fails due to technical issues."""
    pass