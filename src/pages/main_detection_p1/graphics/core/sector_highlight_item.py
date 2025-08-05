"""
Backward compatibility import for sector_highlight_item
This file has been moved to src.pages.main_detection_p1.components.graphics

This compatibility layer will be removed in a future version.
Please update your imports to use the new location.
"""

import warnings

warnings.warn(
    "Importing from src.pages.main_detection_p1.graphics.core.sector_highlight_item is deprecated. "
    "Please import from src.pages.main_detection_p1.components.graphics instead.",
    DeprecationWarning,
    stacklevel=2
)

from src.pages.main_detection_p1.components.graphics.sector_highlight_item import *