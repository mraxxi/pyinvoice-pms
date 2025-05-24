# main_window.py
"""
Main window and invoice form GUI for the Invoice Generator application.
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QLabel, QLineEdit, QPushButton,
                             QFrame, QScrollArea, QMessageBox, QFileDialog,
                             QApplication)
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QIcon

from models import Invoice, LineItem, InvoiceValidator
from widgets import LineItemWidget, TotalDisplayWidget
from pdf_generator import PDFExportManager
import config
import utils


class InvoiceForm(QWidget):
    """Main invoice form widget containing all invoice input fields."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.line_item_widgets = []
        self.pdf_manager = PDFExportManager()
        self._setup_ui()
        self._load_default_invoice()

    def _setup_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()

        # Invoice header section
        main_layout.addLayout(self._create_header_section())

        # Separator
        main_layout.addWidget(self._create_separator())

        # Line items section
        main_layout.addLayout(self._create_line_items_section())

        # Total section
        main_layout.addLayout(self._create_total_section())

        # Actions section
        main_layout.addLayout(self._create_actions_section())

        self.setLayout(main_layout)

    def _create_header_section(self) -> QGridLayout:
        """Create the invoice header input section."""
        header_layout = QGridLayout()

        # Invoice number
        header_layout.addWidget(QLabel("Invoice #:"), 0, 0)
        self.invoice_number = QLineEdit()
        header_layout.addWidget(self.invoice_number, 0, 1)

        # Invoice date
        header_layout.addWidget(QLabel("Date:"), 0, 2)
        self.invoice_date = QLineEdit()
        header_layout.addWidget(self.invoice_date, 0, 3)

        # Customer details
        header_layout.addWidget(QLabel("Customer:"), 1, 0)
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Customer name")
        header_layout.addWidget(self.customer_name, 1, 1)

        header_layout.addWidget(QLabel("Address:"), 1, 2)
        self.customer_address = QLineEdit()
        self.customer_address.setPlaceholderText("Customer address")
        header_layout.addWidget(self.customer_address, 1, 3)

        return header_layout

    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _create_line_items_section(self) -> QVBoxLayout:
        """Create the line items input section."""
        line_items_layout = QVBoxLayout()

        # Headers
        line_items_layout.addLayout(self._create_line_items_headers())

        # Scroll area for line items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.items_layout = QVBoxLayout(self.scroll_content)
        self.items_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)

        line_items_layout.addWidget(self.scroll_area)

        # Add button for new line item
        self.add_item_btn = QPushButton("+ Add Item")
        self.add_item_btn.clicked.connect(self.add_line_item)
        line_items_layout.addWidget(self.add_item_btn)

        return line_items_layout

    def _create_line_items_headers(self) -> QHBoxLayout:
        """Create the headers for the line items table."""
        headers_layout = QHBoxLayout()
        headers = ["#", "Description", "Qty", "Price", "Subtotal", ""]
        widths = [
            config.LINE_ITEM_FIELD_WIDTHS['number'],
            0,  # Description takes remaining space
            config.LINE_ITEM_FIELD_WIDTHS['amount'],
            config.LINE_ITEM_FIELD_WIDTHS['price'],
            config.LINE_ITEM_FIELD_WIDTHS['subtotal'],
            config.LINE_ITEM_FIELD_WIDTHS['delete_btn']
        ]

        for i, header in enumerate(headers):
            label = QLabel(header)
            label.setAlignment(Qt.AlignCenter)

            # Apply bold font to headers
            font = QFont()
            font.setBold(True)
            label.setFont(font)

            if widths[i] > 0:
                label.setFixedWidth(widths[i])

            headers_layout.addWidget(label, 1 if widths[i] == 0 else 0)

        return headers_layout

    def _create_total_section(self) -> QHBoxLayout:
        """Create the total display section."""
        total_layout = QHBoxLayout()

        total_layout.addStretch()

        # Total label
        total_label = QLabel("Total:")
        font = QFont()
        font.setBold(True)
        total_label.setFont(font)
        total_layout.addWidget(total_label)

        # Total display
        self.total_display = QLineEdit("Rp 0")
        self.total_display.setReadOnly(True)
        self.total_display.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['subtotal'])
        self.total_display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Style the total display
        font = QFont()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.total_display.setFont(font)
        total_layout.addWidget(self.total_display)

        # Placeholder for alignment with delete button column
        placeholder = QWidget()
        placeholder.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['delete_btn'])
        total_layout.addWidget(placeholder)

        return total_layout

    def _create_actions_section(self) -> QHBoxLayout:
        """Create the action buttons section."""
        actions_layout = QHBoxLayout()

        # Generate PDF button
        self.generate_pdf_btn = QPushButton("Generate PDF")
        self.generate_pdf_btn.setMinimumWidth(120)
        self.generate_pdf_btn.clicked.connect(self.generate_pdf)
        actions_layout.addWidget(self.generate_pdf_btn)

        # Clear form button
        self.clear_form_btn = QPushButton("Clear Form")
        self.clear_form_btn.setMinimumWidth(120)
        self.clear_form_btn.clicked.connect(self.clear_form)
        actions_layout.addWidget(self.clear_form_btn)

        actions_layout.addStretch()

        return actions_layout

    def _load_default_invoice(self):
        """Load default invoice data into the form."""
        default_invoice = Invoice.create_default()
        self._load_invoice_data(default_invoice)
        self.add_line_item()  # Add the initial line item

    def _load_invoice_data(self, invoice: Invoice):
        """Load invoice data into the form fields."""
        self.invoice_number.setText(invoice.invoice_number)
        self.invoice_date.setText(invoice.invoice_date)
        self.customer_name.setText(invoice.customer_name)
        self.customer_address.setText(invoice.customer_address)

    @pyqtSlot()
    def add_line_item(self):
        """Add a new line item to the invoice."""
        # Create new line item with next number
        line_item = LineItem(
            number=len(self.line_item_widgets) + 1,
            description="",
            amount=config.DEFAULT_QUANTITY,
            price=0
        )

        # Create widget
        widget = LineItemWidget(self, line_item)
        widget.data_changed.connect(self.update_total)
        widget.delete_requested.connect(self.remove_line_item)

        # Add to layout and list
        self.line_item_widgets.append(widget)
        self.items_layout.addWidget(widget)

        # Focus on the new item's description field
        widget.focus_first_empty_field()

        self.update_total()

    @pyqtSlot(object)
    def remove_line_item(self, widget: LineItemWidget):
        """Remove a line item from the invoice."""
        if len(self.line_item_widgets) <= 1:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "At least one line item is required."
            )
            return

        # Remove from list and layout
        self.line_item_widgets.remove(widget)
        self.items_layout.removeWidget(widget)
        widget.deleteLater()

        # Renumber remaining items
        self._renumber_line_items()

        self.update_total()

    def _renumber_line_items(self):
        """Renumber all line items to maintain sequential order."""
        for i, widget in enumerate(self.line_item_widgets):
            widget.set_number(i + 1)

    @pyqtSlot()
    def update_total(self):
        """Update the total invoice amount display."""
        total = sum(widget.get_line_item().subtotal for widget in self.line_item_widgets)
        self.total_display.setText(utils.format_currency(total))

    def get_invoice_data(self) -> Invoice:
        """Get the current invoice data from the form."""
        line_items = [widget.get_line_item() for widget in self.line_item_widgets]

        return Invoice(
            invoice_number=self.invoice_number.text(),
            invoice_date=self.invoice_date.text(),
            customer_name=self.customer_name.text(),
            customer_address=self.customer_address.text(),
            line_items=line_items
        )

    def validate_invoice(self) -> tuple[bool, list]:
        """
        Validate the current invoice data.
        Returns (is_valid, list_of_errors).
        """
        invoice = self.get_invoice_data()
        errors = InvoiceValidator.validate_invoice(invoice)
        return len(errors) == 0, errors

    @pyqtSlot()
    def generate_pdf(self):
        """Generate and save the invoice PDF."""
        # Validate the invoice first
        is_valid, errors = self.validate_invoice()
        if not is_valid:
            error_msg = utils.format_validation_errors(errors)
            QMessageBox.warning(
                self,
                "Validation Error",
                f"Please fix the following issues before generating PDF:\n\n{error_msg}"
            )
            return

        # Get invoice data
        invoice = self.get_invoice_data()

        # Show file dialog to select save location
        default_filename = utils.FileManager.get_default_invoice_filename(
            invoice.invoice_number
        )
        suggested_path = utils.FileManager.suggest_save_location(default_filename)

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Invoice PDF",
            suggested_path,
            "PDF Files (*.pdf)",
            options=options
        )

        if not filename:
            return  # User canceled

        # Generate PDF
        success, message = self.pdf_manager.export_and_open(invoice, filename)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF:\n{message}")

    @pyqtSlot()
    def clear_form(self):
        """Clear the form and reset to default state."""
        reply = QMessageBox.question(
            self,
            "Clear Form",
            "Are you sure you want to clear all data and start over?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Clear customer info
            self.customer_name.clear()
            self.customer_address.clear()

            # Reset invoice info to defaults
            default_invoice = Invoice.create_default()
            self.invoice_number.setText(default_invoice.invoice_number)
            self.invoice_date.setText(default_invoice.invoice_date)

            # Remove all line items
            while self.line_item_widgets:
                widget = self.line_item_widgets[0]
                self.line_item_widgets.remove(widget)
                self.items_layout.removeWidget(widget)
                widget.deleteLater()

            # Add one fresh line item
            self.add_line_item()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._create_central_widget()
        self._setup_menu_bar()
        self._setup_status_bar()

    def _setup_window(self):
        """Configure the main window properties."""
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.setMinimumSize(QSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT))

        # Center the window on screen
        self._center_window()

    def _center_window(self):
        """Center the window on the screen."""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def _create_central_widget(self):
        """Create and set the central widget."""
        self.invoice_form = InvoiceForm(self)
        self.setCentralWidget(self.invoice_form)

    def _setup_menu_bar(self):
        """Setup the menu bar (placeholder for future expansion)."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        # Add actions (placeholder for future features)
        # new_action = file_menu.addAction('New Invoice')
        # open_action = file_menu.addAction('Open Invoice')
        # save_action = file_menu.addAction('Save Invoice')
        # file_menu.addSeparator()
        # exit_action = file_menu.addAction('Exit')

    def _setup_status_bar(self):
        """Setup the status bar."""
        self.statusBar().showMessage("Ready")

    def closeEvent(self, event):
        """Handle the window close event."""
        # In the future, this could check for unsaved changes
        event.accept()