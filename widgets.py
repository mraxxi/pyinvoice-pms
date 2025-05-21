# widgets.py
"""
Custom PyQt widgets for the Invoice Generator application.
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QSpinBox,
                             QDoubleSpinBox, QPushButton)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QFont

from models import LineItem
import config
import utils


class LineItemWidget(QWidget):
    """
    Custom widget representing a single line item in the invoice.
    Emits signals when data changes or when deletion is requested.
    """

    # Signals
    data_changed = pyqtSignal()  # Emitted when any field changes
    delete_requested = pyqtSignal(object)  # Emitted when delete button is clicked

    def __init__(self, parent=None, line_item: LineItem = None):
        super().__init__(parent)
        self.parent = parent
        self._line_item = line_item or LineItem(1, "", config.DEFAULT_QUANTITY, 0.0)
        self._setup_ui()
        self._connect_signals()
        self._update_display()

    def _setup_ui(self):
        """Initialize the UI components."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Number field (read-only)
        self.number_edit = QLineEdit()
        self.number_edit.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['number'])
        self.number_edit.setReadOnly(True)
        self.number_edit.setAlignment(Qt.AlignCenter)

        # Description field
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Item description")

        # Amount field (spinner)
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(config.MIN_QUANTITY, config.MAX_QUANTITY)
        self.amount_spin.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['amount'])

        # Price field
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, config.MAX_PRICE)
        self.price_spin.setPrefix(config.CURRENCY_SYMBOL)
        self.price_spin.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['price'])

        # Subtotal field (read-only)
        self.subtotal_edit = QLineEdit()
        self.subtotal_edit.setReadOnly(True)
        self.subtotal_edit.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['subtotal'])
        self.subtotal_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Make subtotal field visually distinct
        font = QFont()
        font.setBold(True)
        self.subtotal_edit.setFont(font)

        # Delete button
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['delete_btn'])
        self.delete_btn.setToolTip("Delete this line item")

        # Add all widgets to layout
        layout.addWidget(self.number_edit)
        layout.addWidget(self.desc_edit, 1)  # Description takes remaining space
        layout.addWidget(self.amount_spin)
        layout.addWidget(self.price_spin)
        layout.addWidget(self.subtotal_edit)
        layout.addWidget(self.delete_btn)

        self.setLayout(layout)

    def _connect_signals(self):
        """Connect widget signals to slots."""
        self.desc_edit.textChanged.connect(self._on_data_changed)
        self.amount_spin.valueChanged.connect(self._on_data_changed)
        self.price_spin.valueChanged.connect(self._on_data_changed)
        self.delete_btn.clicked.connect(self._on_delete_clicked)

    def _update_display(self):
        """Update the display with current line item data."""
        self.number_edit.setText(str(self._line_item.number))
        self.desc_edit.setText(self._line_item.description)
        self.amount_spin.setValue(self._line_item.amount)
        self.price_spin.setValue(self._line_item.price)
        self._update_subtotal()

    @pyqtSlot()
    def _on_data_changed(self):
        """Handle changes to any data field."""
        # Update the internal model
        self._line_item.description = self.desc_edit.text()
        self._line_item.amount = self.amount_spin.value()
        self._line_item.price = self.price_spin.value()

        # Update subtotal display
        self._update_subtotal()

        # Emit signal to notify parent
        self.data_changed.emit()

    @pyqtSlot()
    def _on_delete_clicked(self):
        """Handle delete button click."""
        self.delete_requested.emit(self)

    def _update_subtotal(self):
        """Update the subtotal display."""
        subtotal_text = utils.format_currency(self._line_item.subtotal)
        self.subtotal_edit.setText(subtotal_text)

    def get_line_item(self) -> LineItem:
        """Get the current line item data."""
        return LineItem(
            number=self._line_item.number,
            description=self.desc_edit.text(),
            amount=self.amount_spin.value(),
            price=self.price_spin.value()
        )

    def set_line_item(self, line_item: LineItem):
        """Set the line item data and update display."""
        self._line_item = line_item
        self._update_display()

    def set_number(self, number: int):
        """Set the line item number."""
        self._line_item.number = number
        self.number_edit.setText(str(number))

    def clear(self):
        """Clear all fields to default values."""
        self.desc_edit.clear()
        self.amount_spin.setValue(config.DEFAULT_QUANTITY)
        self.price_spin.setValue(0.0)
        self._on_data_changed()

    def is_valid(self) -> tuple[bool, list]:
        """
        Check if the current line item data is valid.
        Returns (is_valid, list_of_errors).
        """
        from models import InvoiceValidator
        errors = InvoiceValidator.validate_line_item(self.get_line_item())
        return len(errors) == 0, errors

    def highlight_errors(self, enable: bool = True):
        """
        Highlight fields with validation errors.
        This could be extended to show specific field errors.
        """
        style = "background-color: #ffebee;" if enable else ""

        if not self.desc_edit.text().strip():
            self.desc_edit.setStyleSheet(style)
        else:
            self.desc_edit.setStyleSheet("")

    def focus_first_empty_field(self):
        """Set focus to the first empty required field."""
        if not self.desc_edit.text().strip():
            self.desc_edit.setFocus()
            return

        if self.price_spin.value() == 0:
            self.price_spin.setFocus()
            return


class TotalDisplayWidget(QWidget):
    """Widget to display the total amount with proper formatting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.set_total(0.0)

    def _setup_ui(self):
        """Initialize the UI components."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Total label
        self.label = QLineEdit("Total:")
        self.label.setReadOnly(True)
        self.label.setMaximumWidth(60)

        # Total amount display
        self.amount_display = QLineEdit()
        self.amount_display.setReadOnly(True)
        self.amount_display.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['subtotal'])
        self.amount_display.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Make total display prominent
        font = QFont()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.amount_display.setFont(font)

        layout.addStretch()  # Push total to the right
        layout.addWidget(self.label)
        layout.addWidget(self.amount_display)
        layout.addWidget(QWidget())  # Placeholder for alignment
        layout.setFixedWidth(config.LINE_ITEM_FIELD_WIDTHS['delete_btn'])

        self.setLayout(layout)

    def set_total(self, total: float):
        """Update the displayed total amount."""
        total_text = utils.format_currency(total)
        self.amount_display.setText(total_text)

    def get_total_text(self) -> str:
        """Get the current total as formatted text."""
        return self.amount_display.text()