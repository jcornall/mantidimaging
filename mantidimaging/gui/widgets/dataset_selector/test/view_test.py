# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

from mantidimaging.gui.widgets.dataset_selector.presenter import Notification
from mantidimaging.gui.widgets.dataset_selector.view import DatasetSelectorWidgetView
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class DatasetSelectorWidgetViewTest(unittest.TestCase):

    def setUp(self) -> None:
        self.view = DatasetSelectorWidgetView(None)
        self.view.presenter = self.presenter = mock.Mock()

    def test_subscribe_to_main_window(self):
        main_window_mock = mock.create_autospec(MainWindowView)
        main_window_mock.model_changed.connect = mock.Mock()

        self.view.subscribe_to_main_window(main_window_mock)
        self.presenter.notify.assert_called_once_with(Notification.RELOAD_DATASETS)
        main_window_mock.model_changed.connect.assert_called_once_with(self.view._handle_loaded_datasets_changed)

    def test_unsubscribe_from_main_window(self):
        self.view.main_window = main_window_mock = mock.create_autospec(MainWindowView)
        main_window_mock.model_changed.disconnect = mock.Mock()

        self.view.unsubscribe_from_main_window()
        main_window_mock.model_changed.disconnect.assert_called_once_with(self.view._handle_loaded_datasets_changed)

    def test_handle_loaded_datasets_changed(self):
        self.view._handle_loaded_datasets_changed()
        self.presenter.notify.assert_called_once_with(Notification.RELOAD_DATASETS)

    def test_current(self):
        assert self.view.current() is self.presenter.current_dataset

    def _add_items(self):
        self.view.addItems(["flat_0001", "dark_0001", "tomo_0001"])

    def test_try_to_select_relevant_stack(self):
        self._add_items()
        self.view.try_to_select_relevant_stack("dark")
        self.assertEqual(self.view.currentIndex(), 1)
        self.assertEqual(self.view.currentText(), "dark_0001")

        self.view.try_to_select_relevant_stack("flat")
        self.assertEqual(self.view.currentIndex(), 0)
        self.assertEqual(self.view.currentText(), "flat_0001")

    def test_current_is_strict(self):
        self.assertEqual(self.view.current_is_strict(), self.presenter.current_is_strict)
