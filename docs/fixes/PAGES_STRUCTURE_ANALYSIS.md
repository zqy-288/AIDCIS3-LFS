# 项目页面结构迁移分析报告

## 一、当前 src/pages 目录结构

### 1. 主检测页面 (main_detection_p1) ✅
```
main_detection_p1/
├── __init__.py
├── main_detection_page.py              # 页面主入口
├── native_main_detection_view_p1.py    # 原生三栏式视图
├── native_main_detection_view_refactored.py  # 重构版本
├── components/                         # UI组件目录
│   ├── center_visualization_panel.py   # 中央可视化面板
│   ├── control_panel.py               # 控制面板
│   ├── enhanced_workpiece_diagram.py  # 增强工件图
│   ├── graphics/                      # 图形组件子目录 ⚠️
│   │   ├── complete_panorama_widget.py
│   │   ├── dynamic_sector_view.py
│   │   ├── graphics_view.py
│   │   ├── hole_item.py
│   │   ├── interaction.py
│   │   ├── navigation.py
│   │   ├── scene_manager.py
│   │   ├── sector_highlight_item.py
│   │   ├── sector_overlay.py
│   │   └── view_overlay.py
│   ├── left_info_panel.py            # 左侧信息面板
│   ├── panorama_sector_coordinator.py # 全景扇形协调器
│   ├── right_operations_panel.py     # 右侧操作面板
│   ├── sector_assignment_manager.py   # 扇形分配管理器
│   └── simulation_controller.py       # 模拟控制器
└── services/                          # 服务层
    └── dxf_loader_service.py         # DXF加载服务

### 2. 实时监控页面 (realtime_monitoring_p2) ⚠️
```
realtime_monitoring_p2/
├── __init__.py
├── realtime_monitoring_page.py        # 页面主入口
├── legacy_realtime_monitoring_page.py # 遗留版本
├── test_legacy_functionality.py       # 测试文件
└── test_p2_integration.py            # 集成测试
```
**问题**：缺少 components/ 和 widgets/ 目录，UI组件仍依赖外部模块

### 3. 历史分析页面 (history_analytics_p3) ✅
```
history_analytics_p3/
├── __init__.py
├── history_analytics_page.py          # 页面主入口
├── components/                        # 业务组件
│   ├── data_filter_manager.py
│   ├── export_manager.py
│   ├── quality_metrics_calculator.py
│   ├── statistics_engine.py
│   └── trend_analyzer.py
├── models/                           # 数据模型
│   └── __init__.py
└── widgets/                          # UI小部件
    └── __init__.py
```
**状态**：结构良好，但 widgets/ 目录为空，需要实现具体UI组件

### 4. 报告生成页面 (report_generation_p4) ❌
```
report_generation_p4/
├── __init__.py
└── report_generation_page.py         # 仅有占位符实现
```
**问题**：页面基本未实现，缺少所有必要的组件和子目录

## 二、外部依赖分析

### 1. 对 src/modules 的依赖
- **产品选择对话框**：`src.modules.product_selection.ProductSelectionDialog`
- **内窥镜视图**：`src.modules.endoscope_view.EndoscopeView`
- **实时图表组件**：`src.modules.realtime_chart_p2.components.chart_widget.ChartWidget`
- **全景视图适配器**：`src.modules.panorama_view.legacy_adapter`

### 2. 对 src/core_business/graphics 的依赖
该目录包含大量UI组件，应该迁移到 pages 下：
- `CompletePanoramaWidget` - 完整全景小部件
- `DynamicSectorDisplayWidget` - 动态扇形显示
- `OptimizedGraphicsView` - 优化图形视图
- `ViewOverlayWidget` - 视图覆盖层
- `SectorOverlayWidget` - 扇形覆盖层

### 3. 散落的UI组件
在 src/modules 中发现的主要UI组件：
- `MainDetectionView` - 主检测视图（重复实现）
- `WorkpieceDiagram` - 工件图表
- `HistoryViewer` - 历史查看器
- `ReportManagerWidget` - 报告管理器
- `DxfRenderDialog` - DXF渲染对话框
- `ProductManagement` - 产品管理界面

## 三、迁移建议

### 1. 立即需要迁移的组件

#### P1 页面相关
- [ ] 将 `src/core_business/graphics/` 中的所有UI组件迁移到 `src/pages/main_detection_p1/components/graphics/`
- [ ] 将 `src/modules/workpiece_diagram.py` 迁移到 `src/pages/main_detection_p1/components/`
- [ ] 将 `src/modules/product_selection.py` 迁移到共享组件目录

#### P2 页面相关
- [ ] 创建 `src/pages/realtime_monitoring_p2/components/` 目录
- [ ] 将 `src/modules/endoscope_view.py` 迁移到 `src/pages/realtime_monitoring_p2/components/`
- [ ] 将 `src/modules/realtime_chart_p2/` 整体迁移到 `src/pages/realtime_monitoring_p2/components/chart/`

#### P3 页面相关
- [ ] 实现 `src/pages/history_analytics_p3/widgets/` 中的具体UI组件
- [ ] 将 `src/modules/history_viewer.py` 迁移并整合

#### P4 页面相关
- [ ] 创建完整的目录结构
- [ ] 将 `src/modules/report_manager_widget.py` 迁移
- [ ] 将 `src/modules/report_output_interface.py` 迁移

### 2. 共享组件处理方案

建议创建 `src/pages/shared/` 目录存放跨页面共享组件：
```
src/pages/shared/
├── dialogs/
│   ├── product_selection_dialog.py
│   └── dxf_render_dialog.py
├── widgets/
│   ├── theme_switcher.py
│   └── style_detector.py
└── base/
    └── ui_component_base.py
```

### 3. 业务逻辑分离

需要将以下纯UI组件从 `src/core_business/` 移出：
- `graphics/` 目录下的所有 Widget 类
- `graphics/` 目录下的所有 View 类
- 保留纯业务逻辑的数据处理和算法类

### 4. 导入路径更新

迁移后需要更新所有导入路径：
```python
# 旧路径
from src.modules.product_selection import ProductSelectionDialog
from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget

# 新路径
from src.pages.shared.dialogs.product_selection_dialog import ProductSelectionDialog
from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
```

## 四、执行优先级

1. **高优先级**：
   - P1页面的graphics组件迁移（影响最大）
   - P2页面的组件目录创建和迁移
   - 共享组件目录的建立

2. **中优先级**：
   - P3页面widgets的实现
   - 业务逻辑与UI的进一步分离

3. **低优先级**：
   - P4页面的完整实现
   - 遗留代码的清理

## 五、风险评估

1. **导入循环风险**：迁移时需要特别注意避免循环导入
2. **功能回归风险**：需要充分测试确保功能不受影响
3. **版本控制**：建议在新分支上进行迁移工作

## 六、总结

当前项目的页面结构迁移已部分完成，但仍有大量UI组件散落在 `src/modules/` 和 `src/core_business/` 中。建议按照上述计划逐步将所有UI组件迁移到 `src/pages/` 下的相应位置，实现清晰的模块化结构。