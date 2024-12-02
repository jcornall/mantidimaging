# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from collections.abc import Callable
from logging import getLogger
import numpy as np

from imagecodecs._deflate import DeflateError

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.live_viewer.model import LiveViewerWindowModel, Image_Data
from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.core.data import ImageStack

if TYPE_CHECKING:
    from mantidimaging.gui.windows.live_viewer.view import LiveViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover

logger = getLogger(__name__)


class LiveViewerWindowPresenter(BasePresenter):
    """
    The presenter for the Live Viewer window.

    This presenter is responsible for handling user interaction with the view and
    updating the model and view accordingly to look after the state of the window.
    """
    view: LiveViewerWindowView
    model: LiveViewerWindowModel
    op_func: Callable

    def __init__(self, view: LiveViewerWindowView, main_window: MainWindowView):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = LiveViewerWindowModel(self)
        self.selected_image: Image_Data | None = None
        self.filters = {f.filter_name: f for f in load_filter_packages()}

    def close(self) -> None:
        """Close the window."""
        if self.model is not None:
            self.model.close()
        self.model = None  # type: ignore # Presenter instance to be destroyed -type can be inconsistent
        self.view = None  # type: ignore # Presenter instance to be destroyed -type can be inconsistent

    def set_dataset_path(self, path: Path) -> None:
        """Set the path to the dataset."""
        self.model.path = path

    def clear_label(self) -> None:
        """Clear the label."""
        self.view.label_active_filename.setText("")

    def handle_deleted(self) -> None:
        """Handle the deletion of the image."""
        self.view.remove_image()
        self.clear_label()
        self.view.live_viewer.z_slider.set_range(0, 1)
        self.view.live_viewer.show_error(None)

    def update_image_list(self, images_list: list[Image_Data]) -> None:
        """Update the image in the view."""
        # TODO: Might be a good idea to update and store the image list in the model so it can be cycled through
        if not images_list:
            self.handle_deleted()
            self.view.set_load_as_dataset_enabled(False)
        else:
            self.model.images = images_list
            self.view.set_image_range((0, len(images_list) - 1))
            self.view.set_image_index(len(images_list) - 1)
            self.view.set_load_as_dataset_enabled(True)

    def select_image(self, index: int) -> None:
        if not self.model.images:
            return
        self.selected_image = self.model.images[index]
        if not self.selected_image:
            return
        image_timestamp = self.selected_image.image_modified_time_stamp
        self.view.label_active_filename.setText(f"{self.selected_image.image_name} - {image_timestamp}")

        self.display_image(self.selected_image)

    def display_image(self, image_data_obj: Image_Data) -> None:
        """
        Display image in the view after validating contents
        """
        try:
            image_data = self.model.load_image_from_path(image_data_obj.image_path)
        except (OSError, KeyError, ValueError, DeflateError) as error:
            message = f"{type(error).__name__} reading image: {image_data_obj.image_path}: {error}"
            logger.error(message)
            self.view.remove_image()
            self.view.live_viewer.show_error(message)
            return
        self.view.live_viewer.set_image_shape(image_data.shape)
        if not self.view.live_viewer.roi_object and self.view.spectrum_action.isChecked():
            self.view.live_viewer.add_roi()
        image_data = self.perform_operations(image_data)
        if image_data.size == 0:
            message = "reading image: {image_path}: Image has zero size"
            logger.error("reading image: %s: Image has zero size", image_data_obj.image_path)
            self.view.remove_image()
            self.view.live_viewer.show_error(message)
            return
        self.view.show_most_recent_image(image_data)
        self.update_spectrum(self.model.mean)
        self.view.live_viewer.show_error(None)

    @staticmethod
    @ImageCache
    def load_image_from_path(image_path: Path) -> np.ndarray:
        """
        Load a .Tif, .Tiff or .Fits file only if it exists
        and returns as an ndarray
        """
        if image_path.suffix.lower() in [".tif", ".tiff"]:
            with tifffile.TiffFile(image_path) as tif:
                image_data = tif.asarray()
            return image_data
        elif image_path.suffix.lower() == ".fits":
            with fits.open(image_path) as fits_hdul:
                image_data = fits_hdul[0].data
            return image_data
        else:
            raise ValueError(f"Unsupported file type: {image_path.suffix}")

    def update_image_modified(self, image_path: Path) -> None:
        """
        Update the displayed image when the file is modified
        """
        if self.selected_image and image_path == self.selected_image.image_path:
            self.display_image(self.selected_image)

    def update_image_operation(self) -> None:
        """
        Reload the current image if an operation has been performed on the current image
        """
        if self.selected_image is not None:
            self.display_image(self.selected_image)

    def convert_image_to_imagestack(self, image_data) -> ImageStack:
        """
        Convert the single image to an imagestack so the Operations framework can be used
        """
        image_data_shape = image_data.shape
        image_data_temp = np.zeros(shape=(1, image_data_shape[0], image_data_shape[1]))
        image_data_temp[0] = image_data
        return ImageStack(image_data_temp)

    def perform_operations(self, image_data) -> np.ndarray:
        if not self.view.filter_params:
            return image_data
        image_stack = self.convert_image_to_imagestack(image_data)
        for operation in self.view.filter_params:
            op_class = self.filters[operation]
            op_func = op_class.filter_func
            op_params = self.view.filter_params[operation]["params"]
            op_func(image_stack, **op_params)
        return image_stack.slice_as_array(0)[0]

    def load_as_dataset(self) -> None:
        if self.model.images:
            image_dir = self.model.images[0].image_path.parent
            self.main_window.show_image_load_dialog_with_path(str(image_dir))

    def update_spectrum(self, spec_data: list | np.ndarray):
        self.view.spectrum.clearPlots()
        self.view.spectrum.plot(spec_data)

    def handle_roi_moved(self, force_new_spectrums: bool = False):
        # TODO: should we make all these functions go in the model?
        roi = self.view.live_viewer.get_roi()
        self.model.set_roi(roi)
        self.model.clear_mean()
        self.model.calc_mean_fully()
        self.update_spectrum(self.model.mean)
