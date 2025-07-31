# 协调器初始化时序修复

## 问题描述

在加载 CAP1000 数据时，出现以下警告：
```
WARNING:src.pages.main_detection_p1.native_main_detection_view_p1:⚠️ 协调器未初始化，尝试延迟重试
```

这个警告会重复多次，表明协调器初始化时序有问题。

## 问题分析

1. **原因**：`load_hole_collection` 方法在协调器初始化之前被调用
2. **调用顺序**：
   - `main_detection_page.py` 调用 `native_view.load_hole_collection()`
   - 此时 `coordinator` 还是 `None`，因为它在 `initialize_components()` 中才初始化
   - `_load_default_sector1()` 检测到协调器未初始化，设置延迟重试

## 解决方案

### 1. 提前初始化协调器

在 `__init__` 方法中就创建协调器实例：

```python
def __init__(self, parent=None):
    # ...
    
    # 扇形协调器 - 提前初始化
    self.coordinator = None
    if HAS_REFACTORED_MODULES:
        try:
            self.coordinator = PanoramaSectorCoordinator()
            self.logger.info("✅ 扇形协调器预初始化成功")
        except Exception as e:
            self.logger.error(f"扇形协调器预初始化失败: {e}")
```

### 2. 在 initialize_components 中完成设置

```python
def initialize_components(self):
    # 完成扇形协调器的设置（协调器已在__init__中创建）
    if self.coordinator:
        try:
            # 设置图形视图
            if hasattr(self.center_panel, 'graphics_view'):
                self.coordinator.set_graphics_view(self.center_panel.graphics_view)
            
            # 设置全景组件
            if hasattr(self.left_panel, 'sidebar_panorama'):
                self.coordinator.set_panorama_widget(self.left_panel.sidebar_panorama)
                
            # 连接信号
            self.coordinator.sector_stats_updated.connect(self._on_sector_stats_updated)
            
            self.logger.info("✅ 扇形协调器设置完成")
        except Exception as e:
            self.logger.error(f"扇形协调器设置失败: {e}")
```

## 优势

1. **消除警告**：协调器在数据加载前就已存在
2. **保持功能**：延迟设置视图连接，不影响功能
3. **更清晰的初始化流程**：
   - 创建实例（`__init__`）
   - 设置UI（`setup_ui`）
   - 连接组件（`initialize_components`）

## 注意事项

- 协调器的视图连接仍然需要在UI创建后进行
- 数据加载可以在协调器创建后立即进行
- 延迟加载默认扇形的逻辑保持不变