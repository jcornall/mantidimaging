# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.optional_imports import safe_import
from mantidimaging.core.utility.progress_reporting import Progress

if TYPE_CHECKING:
    from mantidimaging.core.utility.data_containers import ProjectionAngles, ReconstructionParameters, ScalarCoR

LOG = getLogger(__name__)
tomopy = safe_import('tomopy')


class TomopyRecon(BaseRecon):

    @staticmethod
    def find_cor(images: ImageStack, slice_idx: int, start_cor: float, recon_params: ReconstructionParameters) -> float:
        sino = np.maximum(images.sinograms[slice_idx:slice_idx + 1], 1e-6)
        sino = BaseRecon.prepare_sinogram(sino, recon_params)
        return tomopy.find_center(sino,
                                  images.projection_angles(recon_params.max_projection_angle).value,
                                  ind=0,
                                  init=start_cor,
                                  sinogram_order=True)

    @staticmethod
    def single_sino(sino: np.ndarray,
                    cor: ScalarCoR,
                    proj_angles: ProjectionAngles,
                    recon_params: ReconstructionParameters,
                    progress: Progress | None = None) -> np.ndarray:
        sino = BaseRecon.prepare_sinogram(sino, recon_params)
        volume = tomopy.recon(tomo=[sino],
                              sinogram_order=True,
                              theta=proj_angles.value,
                              center=cor.value,
                              algorithm=recon_params.algorithm,
                              filter_name=recon_params.filter_name)

        return volume[0]

    @staticmethod
    def full(images: ImageStack,
             cors: list[ScalarCoR],
             recon_params: ReconstructionParameters,
             progress: Progress | None = None):
        """
        Performs a volume reconstruction using sample data provided as sinograms.

        :param images: Array of sinogram images
        :param cors: Array of centre of rotation values
        :param proj_angles: Array of projection angles
        :param recon_params: Reconstruction Parameters
        :param progress: Optional progress reporter
        :return: 3D image data for reconstructed volume
        """
        progress = Progress.ensure_instance(progress, task_name='TomoPy reconstruction')

        import multiprocessing
        ncores = multiprocessing.cpu_count()

        kwargs = {
            'ncore': ncores,
            'tomo': BaseRecon.prepare_sinogram(images.data, recon_params),
            'sinogram_order': images._is_sinograms,
            'theta': images.projection_angles(recon_params.max_projection_angle).value,
            'center': [cor.value for cor in cors],
            'algorithm': recon_params.algorithm,
            'filter_name': recon_params.filter_name
        }

        with progress:
            volume = tomopy.recon(**kwargs)
            LOG.info(f'Reconstructed 3D volume with shape: {volume.shape}')

        return ImageStack(volume)

    @staticmethod
    def allowed_filters() -> list[str]:
        return ["ramlak", 'shepp', 'cosine', 'hann', 'hamming', 'parzen', 'butterworth']


def allowed_recon_kwargs() -> dict:
    # only gridrec is used from tomopy
    return {'gridrec': ['num_gridx', 'num_gridy', 'filter_name', 'filter_par']}
