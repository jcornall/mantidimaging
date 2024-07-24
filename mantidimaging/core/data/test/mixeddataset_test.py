# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from mantidimaging.core.data.dataset import MixedDataset, _get_stack_data_type
from mantidimaging.test_helpers.unit_test_helper import generate_images


class MixedDatasetTest(unittest.TestCase):

    def setUp(self) -> None:
        self.image_stacks = [generate_images() for _ in range(3)]
        self.mixed_dataset = MixedDataset(stacks=self.image_stacks)

    def test_all(self):
        self.assertListEqual(self.mixed_dataset.all, self.image_stacks)

    def test_delete_stack_from_stacks_list(self):
        prev_stacks = self.image_stacks.copy()
        self.mixed_dataset.delete_stack(self.image_stacks[-1].id)
        self.assertListEqual(self.mixed_dataset.all, prev_stacks[:-1])

    def test_delete_stack_from_recons_list(self):
        [self.mixed_dataset.add_recon(generate_images()) for _ in range(2)]
        recons = self.mixed_dataset.recons.copy()

        id_to_remove = recons[-1].id
        self.mixed_dataset.delete_stack(id_to_remove)
        self.assertNotIn(recons[-1], self.mixed_dataset.all)

    def test_delete_stack_failure(self):
        with self.assertRaises(KeyError):
            self.mixed_dataset.delete_stack("nonexistent-id")

    def test_all_ids(self):
        self.assertListEqual(self.mixed_dataset.all_image_ids, [image_stack.id for image_stack in self.image_stacks])

    def test_sinograms_in_all(self):
        self.assertListEqual(self.mixed_dataset._stacks, self.mixed_dataset.all)
        self.mixed_dataset.sinograms = sinograms = generate_images()
        self.assertListEqual(self.mixed_dataset._stacks + [sinograms], self.mixed_dataset.all)

    def test_delete_sinograms(self):
        self.mixed_dataset.sinograms = sinograms = generate_images()
        self.mixed_dataset.delete_stack(sinograms.id)
        self.assertNotIn(sinograms, self.mixed_dataset.all)

    def test_get_stack_data_type_returns_recon(self):
        recon = generate_images()
        recon_id = recon.id
        dataset = MixedDataset()
        dataset.recons.append(recon)
        self.assertEqual(_get_stack_data_type(recon_id, dataset), "Recon")

    def test_get_stack_data_type_returns_images(self):
        images = generate_images()
        images_id = images.id
        dataset = MixedDataset(stacks=[images])
        self.assertEqual(_get_stack_data_type(images_id, dataset), "Images")
