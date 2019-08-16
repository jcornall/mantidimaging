from enum import Enum
from logging import getLogger
from typing import List, TYPE_CHECKING
from uuid import UUID

import numpy as np
from PyQt5.QtWidgets import QWidget

from mantidimaging.core.data import Images
from mantidimaging.core.utility.histogram import generate_histogram_from_image
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import BlockQtSignals, get_parameters_from_stack
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.windows.savu_filters.job_run_response import JobRunResponseContent
from mantidimaging.gui.windows.savu_filters.model import SavuFiltersWindowModel, CurrentFilterData
from mantidimaging.gui.windows.savu_filters.remote_presenter import SavuFiltersRemotePresenter
from mantidimaging.gui.windows.stack_visualiser import SVParameters, StackVisualiserView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_filters.view import SavuFiltersWindowView
    from mantidimaging.gui.windows.main.view import MainWindowView


class Notification(Enum):
    REGISTER_ACTIVE_FILTER = 1
    APPLY_FILTER = 2
    UPDATE_PREVIEWS = 3
    SCROLL_PREVIEW_UP = 4
    SCROLL_PREVIEW_DOWN = 5


class SavuFiltersWindowPresenter(BasePresenter):
    def __init__(self, view: 'SavuFiltersWindowView',
                 main_window: 'MainWindowView',
                 remote_presenter: SavuFiltersRemotePresenter):
        super(SavuFiltersWindowPresenter, self).__init__(view)

        self.model = SavuFiltersWindowModel(self)
        self.remote_presenter = remote_presenter
        self.main_window = main_window

        self.current_filter: CurrentFilterData = ()

    def notify(self, signal):
        try:
            if signal == Notification.REGISTER_ACTIVE_FILTER:
                self.do_register_active_filter()
            elif signal == Notification.APPLY_FILTER:
                self.do_apply_filter()
            elif signal == Notification.UPDATE_PREVIEWS:
                self.do_update_previews()
            elif signal == Notification.SCROLL_PREVIEW_UP:
                self.do_scroll_preview(1)
            elif signal == Notification.SCROLL_PREVIEW_DOWN:
                self.do_scroll_preview(-1)

        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    @property
    def max_preview_image_idx(self):
        return max(self.model.num_images_in_stack - 1, 0)

    def set_stack_uuid(self, uuid: UUID):
        self.set_stack(self.main_window.get_stack_visualiser(uuid) if uuid is not None else None)

    def set_stack(self, stack: StackVisualiserView):
        # Disconnect ROI update signal from previous stack
        if self.model.stack:
            self.model.stack.roi_updated.disconnect(self.handle_roi_selection)

        # Connect ROI update signal to newly selected stack
        if stack:
            stack.roi_updated.connect(self.handle_roi_selection)

        self.model.stack = stack

        # Update the preview image index
        with BlockQtSignals([self.view]):
            self.set_preview_image_index(0)
            self.view.previewImageIndex.setMaximum(self.max_preview_image_idx)

        self.do_update_previews(False)

    def handle_roi_selection(self, roi):
        if roi:
            # TODO used to check  and self.filter_uses_auto_property(SVParameters.ROI): but disabled for now
            self.view.auto_update_triggered.emit()

    def set_preview_image_index(self, image_idx):
        """
        Sets the current preview image index.
        """
        self.model.preview_image_idx = image_idx

        # Set preview index spin box to new index
        preview_idx_spin = self.view.previewImageIndex
        with BlockQtSignals([preview_idx_spin]):
            preview_idx_spin.setValue(self.model.preview_image_idx)

        # Trigger preview updating
        self.view.auto_update_triggered.emit()

    def do_register_active_filter(self):
        # clear the fields of the previous filter

        filter_idx = self.view.filterSelector.currentIndex()

        savu_filter = self.model.filter(filter_idx)

        parameters_widgets: List[QWidget] = []
        for parameters in savu_filter.visible_parameters():
            label, widget = add_property_to_form(
                parameters.name,
                parameters.type,
                parameters.value,
                tooltip=parameters.description,
                form=self.view.filterPropertiesLayout,
            )
            parameters_widgets.append(widget)

        self.current_filter = (savu_filter, parameters_widgets)
        self.view.set_description(savu_filter.synopsis, savu_filter.info)

        # TODO then trigger self.view.auto_update_triggered.emit to update the view

        # we do not have to do this for SAVU filters as they are all the same #notallfilters
        # Register new filter (adding it's property widgets to the properties layout)
        # TODO set up the filter further if necessary
        # self.model.setup_filter(None)

    def filter_uses_auto_property(self, prop):
        return prop in self.model.auto_props.values() if self.model.auto_props is not None else False

    def do_apply_filter(self):
        self.view.clear_output_text()
        self.model.do_apply_filter(self.current_filter)

    def do_update_previews(self, maintain_axes=True):
        log = getLogger(__name__)

        progress = Progress.ensure_instance()
        progress.task_name = "Filter preview"
        progress.add_estimated_steps(1)

        with progress:
            progress.update(msg="Getting stack")
            stack = self.model.stack_presenter

            # If there is no stack then clear the preview area
            if stack is None:
                self.view.clear_preview_plots()

            else:
                # Add the remaining steps for calculating the preview
                progress.add_estimated_steps(8)

                before_image_data = stack.get_image(self.model.preview_image_idx)

                if maintain_axes:
                    # Record the image axis range from the existing preview
                    # image
                    image_axis_ranges = ((self.view.preview_image_before.get_xlim(),
                                          self.view.preview_image_before.get_ylim())
                                         if self.view.preview_image_before.images else None)

                # Update image before
                self._update_preview_image(before_image_data, self.view.preview_image_before,
                                           self.view.preview_histogram_before, progress)

                # Generate sub-stack and run filter
                progress.update(msg="Running preview filter")
                exec_kwargs = get_parameters_from_stack(stack, self.model.auto_props)

                filtered_image_data = None
                try:
                    sub_images = Images(np.asarray([before_image_data]))
                    self.model.apply_filter(sub_images, exec_kwargs)
                    filtered_image_data = sub_images.sample[0]
                except Exception as e:
                    log.error("Error applying filter for preview: {}".format(e))

                # Update image after
                if filtered_image_data is not None:
                    self._update_preview_image(filtered_image_data, self.view.preview_image_after,
                                               self.view.preview_histogram_after, progress)

                if maintain_axes:
                    # Set the axis range on the newly created image to keep
                    # same zoom level/pan region
                    if image_axis_ranges is not None:
                        self.view.preview_image_before.set_xlim(image_axis_ranges[0])
                        self.view.preview_image_before.set_ylim(image_axis_ranges[1])

            # Redraw
            progress.update(msg="Redraw canvas")
            self.view.canvas.draw()

    def _update_preview_image(self, image_data, image, histogram, progress):
        # Generate histogram data
        progress.update(msg="Generating histogram")
        center, hist, _ = generate_histogram_from_image(image_data)

        # Update image
        progress.update(msg="Updating image")
        # TODO: ideally this should update the data without replotting but a
        # valid image must exist to start with (which may not always happen)
        # and this only works as long as the extents do not change.
        image.cla()
        image.imshow(image_data, cmap=self.view.cmap)

        # Update histogram
        progress.update(msg="Updating histogram")
        histogram.lines[0].set_data(center, hist)
        histogram.relim()
        histogram.autoscale()

    def do_scroll_preview(self, offset):
        idx = self.model.preview_image_idx + offset
        idx = max(min(idx, self.max_preview_image_idx), 0)
        self.set_preview_image_index(idx)

    def do_job_submission_success(self, response_content: JobRunResponseContent):
        self.remote_presenter.do_job_submission_success(response_content)

    def do_job_submission_failure(self, response_content: dict):
        raise NotImplementedError("TODO what do when job submission fails?!")
