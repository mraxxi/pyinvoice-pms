# Invoice Generator

A professional PyQt-based invoice generation application with PDF export functionality, organized in a modular structure for maintainability and scalability.

## Features

- **Dynamic Invoice Creation**: Add/remove line items dynamically
- **Automatic Calculations**: Real-time subtotal and total calculations
- **PDF Export**: Professional PDF generation with A5 format
- **Input Validation**: Comprehensive data validation
- **User-Friendly Interface**: Clean, organized GUI
- **Indonesian Rupiah Support**: Formatted currency display

## Project Structure

```
invoice_generator/
├── main.py              # Application entry point
├── config.py            # Configuration constants
├── models.py            # Data models and business logic
├── widgets.py           # Custom PyQt widgets
├── main_window.py       # Main window and invoice form
├── pdf_generator.py     # PDF generation functionality
├── utils.py             # Utility functions and helpers
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Module Responsibilities

### `main.py`
- Application entry point and startup
- Dependency checking
- Application configuration

### `config.py`
- Configuration constants
- Application settings
- PDF and UI configuration

### `models.py`
- `LineItem`: Represents invoice line items
- `Invoice`: Complete invoice data model
- `InvoiceValidator`: Data validation logic

### `widgets.py`
- `LineItemWidget`: Custom widget for line item input
- `TotalDisplayWidget`: Total amount display widget

### `main_window.py`
- `InvoiceForm`: Main invoice input form
- `MainWindow`: Application main window

### `pdf_generator.py`
- `PDFInvoiceGenerator`: Core PDF generation
- `PDFExportManager`: Export management and file handling

### `utils.py`
- Currency formatting functions
- File management utilities
- Validation helpers
- System integration functions

## Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

## Usage

1. **Invoice Details**: Fill in invoice number, date, and customer information
2. **Line Items**: Add items with description, quantity, and price
3. **Dynamic Updates**: Subtotals and total update automatically
4. **PDF Generation**: Click "Generate PDF" to save and view the invoice

## Requirements

- Python 3.6+
- PyQt5 5.15.0+
- ReportLab 3.6.0+

## Development

The modular structure makes it easy to:

- **Add new features**: Each module has a specific responsibility
- **Modify UI components**: Widgets are separated from business logic
- **Extend PDF formatting**: PDF generation is isolated in its own module
- **Add new data fields**: Models can be extended independently
- **Customize appearance**: Configuration is centralized

## Future Enhancements

The modular structure supports easy addition of:

- Database integration (add `database.py`)
- Template management (add `templates.py`)
- Email functionality (add `email_sender.py`)
- Print preview (extend `pdf_generator.py`)
- Invoice themes (extend `config.py`)
- Data import/export (extend `utils.py`)

## License

This project is provided as-is for educational and commercial use.