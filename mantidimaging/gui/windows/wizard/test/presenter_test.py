# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

from mantidimaging.gui.windows.wizard.presenter import WizardPresenter

WIZARD_DATA = {
    'stages': [{
        'name': 'Loading',
        'steps': [{
            'name': 'Loading files'
        }]
    }, {
        'name': 'Processings',
        'steps': [{
            'name': 'Region of Interest Normalisation'
        }, {
            'name': 'Flat fielding'
        }]
    }]
}


class WizardPresenterTest(unittest.TestCase):

    @mock.patch("mantidimaging.gui.windows.wizard.presenter.WizardView")
    def setUp(self, view: mock.Mock) -> None:
        with mock.patch("mantidimaging.gui.windows.wizard.presenter.WizardPresenter.populate") as _:
            with mock.patch("mantidimaging.gui.windows.wizard.presenter.WizardPresenter.handle_stack_change") as _:
                self.presenter = WizardPresenter(mock.Mock())

    def test_show(self):
        self.presenter.view.show.reset_mock()
        self.presenter.show()
        self.presenter.view.show.assert_called_once()

    def test_populate(self):
        self.presenter.wizard_data = WIZARD_DATA

        stage_calls = []
        step_calls = []
        for stage in WIZARD_DATA["stages"]:
            stage_calls.append(mock.call(stage["name"]))
            for step in stage["steps"]:
                step_calls.append(mock.call(stage["name"], step))

        self.presenter.populate()
        self.presenter.view.add_stage.assert_has_calls(stage_calls)
        self.presenter.view.add_step.assert_has_calls(step_calls)

    def test_run_action(self):
        self.presenter.run_action("load")
        self.presenter.main_window_presenter.wizard_action_load.assert_called_once()

        self.presenter.run_action("operations:ROI Normalisation")
        self.presenter.main_window_presenter.show_operation.assert_called_once_with("ROI Normalisation")

        self.presenter.run_action("reconstruction")
        self.presenter.main_window_presenter.wizard_action_show_reconstruction.assert_called_once()

    def test_handle_stack_change(self):
        mock_stack_dark = mock.Mock()
        mock_stack_dark.name = "Flat"
        mock_stack_dark.metadata = "Flat_history"
        mock_stack_tomo = mock.Mock()
        mock_stack_tomo.name = "Tomo"
        mock_stack_tomo.metadata = "Tomo_history"
        self.presenter.main_window_presenter.get_all_stacks.return_value = [mock_stack_dark, mock_stack_tomo]

        mock_stage = mock.Mock()
        self.presenter.view.stages.values.return_value = [mock_stage]

        self.presenter.handle_stack_change()
        mock_stage.handle_stack_change.assert_called_with("Tomo_history")
