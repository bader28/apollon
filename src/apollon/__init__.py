# Licensed under the terms of the BSD-3-Clause license.
# Copyright (C) 2019 Michael Blaß
# mblass@posteo.net

"""
Apollon feature extraction framework.
"""

import os as _os

try:
    from importlib.metadata import version as _version, PackageNotFoundError
except ImportError:                       # Python < 3.8 fallback
    from importlib_metadata import version as _version, PackageNotFoundError

# The PyPI distribution is named "bader-apollon" (the original "apollon" is
# owned by the upstream project); fall back to "apollon" for older installs.
try:
    __version__ = _version("bader-apollon")
except PackageNotFoundError:
    try:
        __version__ = _version("apollon")
    except PackageNotFoundError:
        __version__ = "0.1.5"

APOLLON_PATH = _os.path.dirname(_os.path.realpath(__file__))
