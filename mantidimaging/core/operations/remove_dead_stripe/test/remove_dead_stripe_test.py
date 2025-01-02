# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.remove_dead_stripe import RemoveDeadStripesFilter
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool


@start_multiprocessing_pool
class RemoveDeadStripesTest(unittest.TestCase):
    """
    Test stripe removal filter.

    Tests that it executes and returns a valid object, but does not verify the numerical results.
    """

    def test_executed(self):
        images = th.generate_images((10, 400, 500))
        control = images.copy()

        # size=3 makes sure that the data will be changed, as the default kernel is bigger
        # than the size of the test data. This requires a large enough test dataset to pass on Windows
        result = RemoveDeadStripesFilter.filter_func(images, size=3)

        th.assert_not_equals(result.data, control.data)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        snr = mock.Mock()
        snr.value = mock.Mock(return_value=3)
        size = mock.Mock()
        size.value = mock.Mock(return_value=61)
        execute_func = RemoveDeadStripesFilter.execute_wrapper(snr, size)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(snr.value.call_count, 1)
        self.assertEqual(size.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()
