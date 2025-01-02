# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QTableView


class RemovableRowTableView(QTableView):

    def keyPressEvent(self, e) -> None:
        super().keyPressEvent(e)

        # Handle deletion of a row from the table by pressing the [Delete] key
        if e.key() == Qt.Key.Key_Delete:
            self.removeSelectedRows()

    def removeSelectedRows(self) -> None:
        """
        Removes all selected rows from the table.
        """
        for row in self.selectionModel().selectedRows():
            self.model().removeRows(row.row(), 1, QModelIndex())
