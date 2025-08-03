# Sector Statistics Display Issue Fix

## Problem
When clicking on a sector, the statistics show `total=6274` (all holes) instead of just the holes in that specific sector.

## Root Cause Analysis

1. **PanoramaSectorCoordinator** correctly:
   - Gets sector-specific holes from `sector_holes_map` (line 111)
   - Calculates stats for only those holes (line 125)
   - Emits the correct stats dict (line 126)

2. **Issue Location**: The problem is in how the stats are displayed in the UI.

3. **Data Flow**:
   ```
   PanoramaSectorCoordinator.set_current_sector()
   ↓
   sector_holes = self.sector_holes_map.get(sector, [])  # Correct: sector-specific holes
   ↓
   stats = self._calculate_sector_stats(sector_holes)    # Correct: stats for those holes
   ↓
   self.sector_stats_updated.emit(stats)                  # Emits correct stats dict
   ↓
   NativeMainDetectionViewP1._on_sector_stats_updated(stats)
   ↓
   self.left_panel.update_sector_stats(stats)            # Updates table with correct data
   ```

## The Fix

The issue was in the `update_sector_stats` method in NativeLeftInfoPanel. It was not properly using the 'total' value from the stats dict when provided. I've updated it to:

1. First check if 'total' is provided in the stats dict
2. Use that value directly if available
3. Only calculate total from other fields if 'total' is not provided

## Verification Steps

1. Load a DXF file with multiple sectors
2. Click on a specific sector
3. Check that the sector statistics table shows:
   - Total: Number of holes in that sector only (not 6274)
   - Correct counts for qualified, defective, pending, etc.

## Code Changes

**File**: `src/pages/main_detection_p1/native_main_detection_view_p1.py`

**Method**: `NativeLeftInfoPanel.update_sector_stats()`

Changed the logic to prioritize the 'total' value from the stats dict when available, ensuring the correct sector-specific total is displayed.