# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import inspect


def call_with_known_parameters(func, **kwargs):
    sig = inspect.signature(func)
    params = sig.parameters.keys()
    ka = {k: v for k, v in kwargs.items() if k in params}
    return func(**ka)
