"""
Core hardware abstraction layer

Contains hardware drivers, device interfaces, and hardware configuration.
This layer provides abstraction over physical devices and hardware libraries.

Directory structure:
- Release/: Compiled hardware libraries and configuration files
  - ConfocalDLL_x64.dll: Confocal microscope driver
  - EBDConfocal_x64.dll: Extended confocal functionality
  - LEMotion_x64.dll: Motion control system
  - KSJApi64u.dll: Camera API
  - And other hardware-specific DLLs and configurations

Note: This is a hardware abstraction layer containing binary drivers.
Python interfaces for these hardware components should be implemented
in the application layers (pages/) or shared services as needed.
"""

__all__ = []