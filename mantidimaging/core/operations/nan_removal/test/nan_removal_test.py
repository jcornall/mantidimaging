# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

import numpy
import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.nan_removal import NaNRemovalFilter


class NaNRemovalFilterTest(unittest.TestCase):

    def test_replace_nans(self):
        images = th.generate_images()
        images.data[::, 0] = numpy.nan
        nan_idxs = np.isnan(images.data)

        result = NaNRemovalFilter().filter_func(images, 3.0)
        self.assertFalse(np.any(np.isnan(result.data)))
        npt.assert_allclose(result.data[nan_idxs], 3.0)

    def test_unknown_mode(self):
        images = th.generate_images()
        self.assertRaises(ValueError, NaNRemovalFilter().filter_func, images, 3.0, "badmode")

    def test_replace_nans_with_median(self):
        images = th.generate_images()
        images.data[:] = 7
        images.data[3, 4, 5] = numpy.nan

        NaNRemovalFilter().filter_func(images, 0, "Median")

        self.assertEqual(images.data[3, 4, 5], 7)
        self.assertTrue(np.all(images.data == 7))
