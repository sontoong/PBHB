# pylint: disable=C0114,C0116,C0301,C0115

import tkinter as tk
from tkinter import ttk


class EntryWithLabel(ttk.Frame):
    def __init__(self, parent, label_text, labelPosition='left', **kwargs):
        super().__init__(parent)

        # Create the label and entry
        self.label = ttk.Label(self, text=label_text)
        self.entry = ttk.Entry(self, **kwargs)

        # Configure label positioning
        if labelPosition == 'left':
            self.label.pack(side=tk.LEFT, padx=(0, 10))
            self.entry.pack(side=tk.LEFT)
        elif labelPosition == 'right':
            self.entry.pack(side=tk.LEFT)
            self.label.pack(side=tk.LEFT, padx=(10, 0))
        elif labelPosition == 'top':
            self.label.pack(side=tk.TOP, pady=(0, 5))
            self.entry.pack(side=tk.TOP, fill=tk.X)
        elif labelPosition == 'bottom':
            self.entry.pack(side=tk.TOP, fill=tk.X)
            self.label.pack(side=tk.TOP, pady=(5, 0))
        else:
            raise ValueError(
                f"Invalid labelPosition: {labelPosition}. Must be 'left', 'right', 'top', or 'bottom'.")

    def get(self):
        """Get the value from the entry widget."""
        return self.entry.get()

    def set(self, value):
        """Set the value of the entry widget."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)


class NumberEntry(ttk.Frame):
    """
    A custom entry widget that only allows numeric input.

    :param label_text: Text for the label
    :param min_value: minimum value
    :param max_value: maximum value
    :param labelPosition: position of the label ('left', 'right', 'top', 'bottom')
    """

    def __init__(self, parent, label_text, min_value=None, max_value=None, labelPosition='left', **kwargs):
        # Get the additional 'min_value' and 'max_value' arguments if they exist
        self.min_value = min_value
        self.max_value = max_value

        # Call the parent constructor
        super().__init__(parent, **kwargs)

        # Create a StringVar to hold the entry value
        self.var = tk.StringVar()

        # Create label and entry
        self.label = ttk.Label(self, text=label_text)

        # Register the validation function to only allow numeric input
        validate_command = (self.register(self._validate), '%P')

        self.entry = ttk.Entry(self, validate='key', textvariable=self.var,
                               validatecommand=validate_command, **kwargs)

        # Configure label positioning
        if labelPosition == 'left':
            self.label.pack(side=tk.LEFT, padx=(0, 10))
            self.entry.pack(side=tk.LEFT)
        elif labelPosition == 'right':
            self.entry.pack(side=tk.LEFT)
            self.label.pack(side=tk.LEFT, padx=(10, 0))
        elif labelPosition == 'top':
            self.label.pack(side=tk.TOP, pady=(0, 5))
            self.entry.pack(side=tk.TOP, fill=tk.X)
        elif labelPosition == 'bottom':
            self.entry.pack(side=tk.TOP, fill=tk.X)
            self.label.pack(side=tk.TOP, pady=(5, 0))
        else:
            raise ValueError(
                f"Invalid labelPosition: {labelPosition}. Must be 'left', 'right', 'top', or 'bottom'.")

    def _validate(self, value):
        """
        Validation function to ensure only numbers are entered within optional min and max range.
        """
        if value == "" or value.isdigit():
            if value:
                number = int(value)
                # Check for min and max value constraints
                if (self.min_value is not None and number < self.min_value) or \
                   (self.max_value is not None and number > self.max_value):
                    return False
            return True
        else:
            return False

    def get(self):
        """Get the current integer value of the entry, or None if empty."""
        value = self.var.get()
        return int(value) if value.isdigit() else None

    def set(self, value):
        """Set the current value of the entry."""
        self.var.set(str(value))

    def trace_add(self, mode, callback):
        """Add a trace to the variable"""
        return self.var.trace_add(mode, lambda name, index, mode: callback())
