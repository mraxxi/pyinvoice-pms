# config.py
"""
Configuration constants for the Invoice Generator application.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# Application Configuration
APP_NAME = "Invoice Generator"
APP_VERSION = "1.0.0"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

# Invoice Configuration
DEFAULT_QUANTITY = 1
MIN_QUANTITY = 1
MAX_QUANTITY = 999
MAX_PRICE = 999999999

# PDF Configuration
PDF_PAGE_SIZE = A4
PDF_MARGINS = {
    'right': 12 * mm,
    'left': 12 * mm,
    'top': 12 * mm,
    'bottom': 12 * mm
}

# Table column widths for PDF (in mm)
PDF_COLUMN_WIDTHS = [10*mm, 70*mm, 15*mm, 30*mm, 30*mm]

# UI Configuration
LINE_ITEM_FIELD_WIDTHS = {
    'number': 40,
    'amount': 70,
    'price': 150,
    'subtotal': 150,
    'delete_btn': 30
}

# Currency Configuration
CURRENCY_SYMBOL = "Rp "
# CURRENCY_FORMAT = ":"
CURRENCY_FORMAT = "{:,.0f}"

# Date Configuration
DATE_FORMAT = "%Y-%m-%d"
INVOICE_DATE_FORMAT = "%Y%m%d"