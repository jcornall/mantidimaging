# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import List, Tuple, Union
from unittest import mock

import pytest

from mantidimaging.core.parallel.utility import execute_impl, multiprocessing_necessary


@pytest.mark.parametrize(
    'shape,cores,should_be_parallel',
    (
        [(100, 10, 10), 1, False],  # forcing 1 core should always return False
        # shapes <= 10 should return False
        [(10, 10, 10), 12, False],
        [10, 12, False],
        # shapes over 10 should return True
        [(11, 10, 10), 12, True],
        [11, 12, True],
        # repeat from above but with list, to cover that branch of the if
        [[100, 10, 10], 1, False],
        [[10, 10, 10], 12, False],
        [[11, 10, 10], 12, True],
    ))
def test_correctly_chooses_parallel(shape: Union[int, List, Tuple[int, int, int]], cores: int,
                                    should_be_parallel: bool):
    assert multiprocessing_necessary(shape, cores) is should_be_parallel


@mock.patch('mantidimaging.core.parallel.utility.Pool')
def test_execute_impl_one_core(mock_pool):
    mock_partial = mock.Mock()
    mock_progress = mock.Mock()
    execute_impl(1, mock_partial, 1, 1, mock_progress, "Test")
    mock_partial.assert_called_once_with(0)
    mock_progress.update.assert_called_once_with(1, "Test")


@mock.patch('mantidimaging.core.parallel.utility.Pool')
def test_execute_impl_par(mock_pool):
    mock_partial = mock.Mock()
    mock_progress = mock.Mock()
    mock_pool_instance = mock.Mock()
    mock_pool_instance.imap.return_value = range(15)
    mock_pool.return_value.__enter__.return_value = mock_pool_instance
    execute_impl(15, mock_partial, 10, 1, mock_progress, "Test")
    mock_pool_instance.imap.assert_called_once()
    assert mock_progress.update.call_count == 15


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
