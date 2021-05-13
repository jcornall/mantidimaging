# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.core.operations.median_filter.median_filter import KernelSpinBox
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MedianKernelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.size_kernel = KernelSpinBox(on_change=mock.Mock())

    def test_default_kernel_size(self):
        self.assertEqual(self.size_kernel.value(), 3)

    def test_increase_jumps_by_two(self):
        self.size_kernel.stepUp()
        self.assertEqual(self.size_kernel.value(), 5)

    def test_minimum_value_of_three(self):
        self.size_kernel.stepDown()
        self.assertEqual(self.size_kernel.value(), 3)

    def test_even_numbers_rejected(self):
        for even_num_str in [str(i) for i in range(2, 10, 2)]:
            self.size_kernel.lineEdit().setText(even_num_str)
            self.assertEqual(self.size_kernel.value(), 3)
