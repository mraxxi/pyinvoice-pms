# models.py
"""
Data models for the Invoice Generator application.
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime
import config


@dataclass
class LineItem:
    """Represents a single line item in an invoice."""
    number: int
    description: str
    amount: int
    price: int

    @property
    def subtotal(self) -> int:
        """Calculate and return the subtotal (amount * price)."""
        return self.amount * self.price

    def to_dict(self) -> dict:
        """Convert the line item to a dictionary."""
        return {
            "number": self.number,
            "description": self.description,
            "amount": self.amount,
            "price": self.price,
            "subtotal": self.subtotal
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'LineItem':
        """Create a LineItem from a dictionary."""
        return cls(
            number=data["number"],
            description=data["description"],
            amount=data["amount"],
            price=data["price"]
        )


@dataclass
class Invoice:
    """Represents a complete invoice with all its details."""
    invoice_number: str
    invoice_date: str
    customer_name: str
    customer_address: str
    line_items: List[LineItem]

    @property
    def total(self) -> float:
        """Calculate and return the total invoice amount."""
        return sum(item.subtotal for item in self.line_items)

    def add_line_item(self, line_item: LineItem) -> None:
        """Add a line item to the invoice."""
        self.line_items.append(line_item)

    def remove_line_item(self, index: int) -> bool:
        """Remove a line item by index. Returns True if successful."""
        if 0 <= index < len(self.line_items) and len(self.line_items) > 1:
            del self.line_items[index]
            self._renumber_items()
            return True
        return False

    def _renumber_items(self) -> None:
        """Renumber all line items to maintain sequential order."""
        for i, item in enumerate(self.line_items):
            item.number = i + 1

    def to_dict(self) -> dict:
        """Convert the invoice to a dictionary."""
        return {
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "customer_name": self.customer_name,
            "customer_address": self.customer_address,
            "line_items": [item.to_dict() for item in self.line_items],
            "total": self.total
        }

    @classmethod
    def create_default(cls) -> 'Invoice':
        """Create a default invoice with current date and one empty line item."""
        today = datetime.now()
        invoice_number = f"INV-{today.strftime(config.INVOICE_DATE_FORMAT)}"
        invoice_date = today.strftime(config.DATE_FORMAT)

        default_item = LineItem(
            number=1,
            description="",
            amount=config.DEFAULT_QUANTITY,
            price=0
        )

        return cls(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            customer_name="",
            customer_address="",
            line_items=[default_item]
        )


class InvoiceValidator:
    """Validator class for invoice data."""

    @staticmethod
    def validate_line_item(line_item: LineItem) -> List[str]:
        """Validate a line item and return list of error messages."""
        errors = []

        if not line_item.description.strip():
            errors.append("Description cannot be empty")

        if line_item.amount < config.MIN_QUANTITY:
            errors.append(f"Amount must be at least {config.MIN_QUANTITY}")

        if line_item.amount > config.MAX_QUANTITY:
            errors.append(f"Amount cannot exceed {config.MAX_QUANTITY}")

        if line_item.price < 0:
            errors.append("Price cannot be negative")

        if line_item.price > config.MAX_PRICE:
            errors.append(f"Price cannot exceed {config.MAX_PRICE}")

        return errors

    @staticmethod
    def validate_invoice(invoice: Invoice) -> List[str]:
        """Validate an invoice and return list of error messages."""
        errors = []

        if not invoice.invoice_number.strip():
            errors.append("Invoice number cannot be empty")

        if not invoice.customer_name.strip():
            errors.append("Customer name cannot be empty")

        if not invoice.line_items:
            errors.append("Invoice must have at least one line item")

        # Validate each line item
        for i, item in enumerate(invoice.line_items):
            item_errors = InvoiceValidator.validate_line_item(item)
            for error in item_errors:
                errors.append(f"Line {i + 1}: {error}")

        return errors