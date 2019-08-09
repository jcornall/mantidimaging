from functools import partial

from . import crop_coords


def _gui_register(form, on_change):
    from mantidimaging.gui.windows.stack_visualiser import SVParameters
    from mantidimaging.gui.utility import add_property_to_form

    add_property_to_form(
            'Select ROI on stack visualiser.', 'label', form=form)

    def custom_execute():
        return partial(crop_coords.execute_single)

    params = {
        'region_of_interest': SVParameters.ROI
    }

    return (params, None, custom_execute, None)
