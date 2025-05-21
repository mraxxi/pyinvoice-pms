# utils.py
"""
Utility functions for the Invoice Generator application.
"""

import sys
import os
import subprocess
from datetime import datetime
from typing import Optional
import config


def format_currency(amount: float) -> str:
    """Format a number as currency string."""
    return f"{config.CURRENCY_SYMBOL}{config.CURRENCY_FORMAT.format(amount)}"


def parse_currency(currency_str: str) -> float:
    """Parse a currency string to float value."""
    try:
        # Remove currency symbol and commas, then convert to float
        clean_str = currency_str.replace(config.CURRENCY_SYMBOL, "").replace(",", "")
        return float(clean_str)
    except (ValueError, AttributeError):
        return 0.0


def generate_invoice_number(prefix: str = "INV") -> str:
    """Generate a default invoice number with current date."""
    today = datetime.now()
    return f"{prefix}-{today.strftime(config.INVOICE_DATE_FORMAT)}"


def get_current_date() -> str:
    """Get current date formatted for invoices."""
    return datetime.now().strftime(config.DATE_FORMAT)


def validate_numeric_input(value: str, min_val: float = 0, max_val: float = float('inf')) -> tuple[bool, float]:
    """
    Validate numeric input string.
    Returns (is_valid, parsed_value).
    """
    try:
        num_value = float(value)
        if min_val <= num_value <= max_val:
            return True, num_value
        return False, 0.0
    except (ValueError, TypeError):
        return False, 0.0


def open_file_with_default_app(filepath: str) -> bool:
    """
    Open a file with the default system application.
    Returns True if successful, False otherwise.
    """
    try:
        if sys.platform == 'win32':
            os.startfile(filepath)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(('open', filepath))
        else:  # Linux and other Unix-like systems
            subprocess.call(('xdg-open', filepath))
        return True
    except Exception:
        return False


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure that a directory exists, creating it if necessary.
    Returns True if directory exists or was created successfully.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except OSError:
        return False


def get_safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename by removing/replacing invalid characters.
    """
    # Characters that are invalid in filenames on most systems
    invalid_chars = '<>:"/\\|?*'
    safe_filename = filename

    for char in invalid_chars:
        safe_filename = safe_filename.replace(char, '_')

    # Remove leading/trailing whitespace and dots
    safe_filename = safe_filename.strip(' .')

    # Ensure the filename is not empty
    if not safe_filename:
        safe_filename = "invoice"

    return safe_filename


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding suffix if truncated.
    """
    if len(text) <= max_length:
        return text

    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]

    return text[:truncate_at] + suffix


class FileManager:
    """Utility class for file operations."""

    @staticmethod
    def get_default_invoice_filename(invoice_number: str) -> str:
        """Generate a default filename for an invoice PDF."""
        safe_number = get_safe_filename(invoice_number.replace('-', '_'))
        return f"Invoice_{safe_number}.pdf"

    @staticmethod
    def get_user_documents_path() -> Optional[str]:
        """Get the user's Documents directory path."""
        try:
            if sys.platform == 'win32':
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    return winreg.QueryValueEx(key, "Personal")[0]
            else:
                home = os.path.expanduser("~")
                docs_path = os.path.join(home, "Documents")
                if os.path.exists(docs_path):
                    return docs_path
                return home
        except Exception:
            return None

    @staticmethod
    def suggest_save_location(filename: str) -> str:
        """Suggest a good default location to save files."""
        docs_path = FileManager.get_user_documents_path()
        if docs_path:
            return os.path.join(docs_path, filename)
        return filename


def log_error(error_message: str, exception: Exception = None) -> None:
    """
    Log error messages for debugging purposes.
    In a production app, this might write to a log file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[ERROR {timestamp}] {error_message}")
    if exception:
        print(f"[ERROR {timestamp}] Exception details: {str(exception)}")


def format_validation_errors(errors: list) -> str:
    """Format a list of validation errors into a readable string."""
    if not errors:
        return ""

    if len(errors) == 1:
        return errors[0]

    formatted = "The following issues were found:\n"
    for i, error in enumerate(errors, 1):
        formatted += f"{i}. {error}\n"

    return formatted.strip()