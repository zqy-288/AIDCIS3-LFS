# 初始视图显示问题分析报告

## 问题描述
加载DXF文件后，显示的是整个管板（宏观视图）而不是预期的扇形（微观视图）。

## 根本原因分析

### 1. 加载流程中的问题

#### 1.1 load_hole_collection 方法中的逻辑问题
```python
# 在 load_hole_collection 方法中：
if is_micro_view:
    # 微观视图模式：加载数据但不显示，等待扇形选择
    graphics_view.current_view_mode = 'micro'
    graphics_view.disable_auto_fit = True
    
    # 先加载所有数据
    graphics_view.load_holes(self.current_hole_collection)
    
    # 然后隐藏所有项，等待扇形选择
    if hasattr(graphics_view, 'scene') and callable(graphics_view.scene):
        scene = graphics_view.scene()
        if scene:
            for item in scene.items():
                item.setVisible(False)
```

#### 1.2 graphics_view 的 load_holes 方法问题
在 `graphics_view.py` 的 `load_holes` 方法中：
```python
# 默认适配到窗口宽度（防抖机制会处理延迟）
if not getattr(self, 'disable_auto_fit', False):
    # 检查是否在微观视图模式
    if hasattr(self, 'current_view_mode') and self.current_view_mode == 'micro':
        self.logger.info("微观视图模式，跳过load_holes时的自动适配")
    else:
        self.fit_to_window_width()
```

虽然设置了 `disable_auto_fit = True`，但是 `load_holes` 方法中还会检查 `current_view_mode`。

### 2. 问题发生的时机

1. **初始状态**：程序启动时，视图按钮状态可能还未初始化
2. **加载数据时**：虽然设置了 `disable_auto_fit = True`，但可能有其他地方触发了视图适配
3. **显示扇形时**：`_show_sector_in_view` 方法中恢复 `disable_auto_fit = False` 的时机可能过早

### 3. 关键问题点

1. **防抖机制延迟**：`fit_to_window_width` 使用了 150ms 的防抖延迟
2. **状态恢复时机**：`disable_auto_fit` 在 500ms 后恢复，可能在这期间触发了其他适配
3. **初始化顺序**：按钮状态可能在加载数据后才正确设置

## 解决方案

### 方案1：确保微观视图模式在加载时就正确设置
```python
def load_hole_collection(self, hole_collection):
    """加载孔位数据到视图"""
    # 更新当前孔位集合
    self.current_hole_collection = hole_collection
    
    # 1. 首先确保视图模式正确设置
    if self.center_panel:
        # 强制设置为微观视图模式
        self.center_panel.micro_view_btn.setChecked(True)
        self.center_panel.macro_view_btn.setChecked(False)
        self.center_panel.current_view_mode = "micro"
        
        # 确保 graphics_view 的模式也正确
        if hasattr(self.center_panel, 'graphics_view') and self.center_panel.graphics_view:
            self.center_panel.graphics_view.current_view_mode = 'micro'
            self.center_panel.graphics_view.disable_auto_fit = True
    
    # 2. 加载数据到协调器
    if self.coordinator and hole_collection:
        self.coordinator.load_hole_collection(hole_collection)
    
    # 3. 加载数据到视图（确保不会触发自动适配）
    if self.center_panel and hasattr(self.center_panel, 'graphics_view'):
        graphics_view = self.center_panel.graphics_view
        
        # 停止所有可能的定时器
        if hasattr(graphics_view, '_fit_timer'):
            graphics_view._fit_timer.stop()
            graphics_view._fit_pending = False
        
        # 加载数据
        graphics_view.load_holes(self.current_hole_collection)
        
        # 隐藏所有项
        scene = graphics_view.scene() if callable(graphics_view.scene) else graphics_view.scene
        if scene:
            for item in scene.items():
                item.setVisible(False)
    
    # 4. 立即显示默认扇形（不延迟）
    self._load_default_sector1()
```

### 方案2：修改 _show_sector_in_view 的恢复时机
```python
def _show_sector_in_view(self, sector):
    """在视图中显示指定扇形"""
    # ... 现有代码 ...
    
    # 适配视图到扇形区域
    graphics_view.fitInView(bounding_rect, Qt.KeepAspectRatio)
    
    # 延迟更长时间再恢复 disable_auto_fit
    # 或者根本不恢复，让它保持禁用状态
    # QTimer.singleShot(500, lambda: setattr(graphics_view, 'disable_auto_fit', False))
```

### 方案3：在 graphics_view 中增加更严格的检查
```python
def fit_to_window_width(self):
    """适配到窗口宽度"""
    # 添加更严格的微观视图检查
    if self.current_view_mode == 'micro':
        self.logger.info("微观视图模式下禁止 fit_to_window_width")
        return
    
    # 现有的 disable_auto_fit 检查
    if getattr(self, 'disable_auto_fit', False):
        self.logger.info("跳过自动适配（disable_auto_fit=True）")
        return
```

## 推荐的综合修复方案

1. **确保初始化顺序正确**：在加载数据前就设置好视图模式
2. **加强微观视图模式检查**：在所有可能触发全视图适配的地方添加检查
3. **优化 disable_auto_fit 的管理**：考虑使用更持久的状态管理，而不是临时标志
4. **移除不必要的延迟恢复**：在微观视图模式下，保持 disable_auto_fit = True

## 测试建议

1. 测试加载 DXF 文件后的初始显示
2. 测试切换视图模式的响应
3. 测试扇形选择和显示的正确性
4. 测试在不同时机加载数据的表现