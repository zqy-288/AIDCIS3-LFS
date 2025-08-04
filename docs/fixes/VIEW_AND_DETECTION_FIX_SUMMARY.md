# 视图和检测顺序修复总结

## 修复时间
2025-07-31

## 问题描述

### 问题1：默认视图问题
- **现象**：用户加载DXF文件后，程序显示宏观视图（整个圆形管板）
- **期望**：应该默认显示微观视图（放大的扇形区域）
- **影响**：用户体验不佳，需要手动切换到微观视图

### 问题2：检测顺序问题  
- **现象**：检测从BC098R164（B区，下半部分）开始
- **期望**：应该从AC098R164（A区，上半部分）开始
- **影响**：不符合标准检测流程，A区应该优先检测

## 根本原因分析

### 1. 视图问题原因
- 在 `load_hole_collection` 方法中，视图模式检查逻辑存在缺陷
- 当按钮状态未初始化时，默认使用了宏观视图
- 宏观视图会调用 `fit_in_view_with_margin()` 显示全部内容

### 2. 检测顺序问题原因
- **坐标系混淆**：
  - 物理坐标系：Y轴向上，A侧（上半部分）y>0，B侧（下半部分）y<0
  - Qt坐标系：Y轴向下，屏幕上方y<0，屏幕下方y>0
- **代码错误**：`_parse_hole_position` 方法中使用了物理坐标系的判定逻辑
- 导致A/B侧判定相反，B侧被错误地优先处理

## 修复方案

### 1. 修复默认视图（文件：`src/pages/main_detection_p1/native_main_detection_view_p1.py`）

```python
# 修改前：
is_micro_view = (self.center_panel and 
                hasattr(self.center_panel, 'micro_view_btn') and 
                self.center_panel.micro_view_btn.isChecked())

# 修改后：
is_micro_view = True  # 默认使用微观视图
if self.center_panel and hasattr(self.center_panel, 'micro_view_btn'):
    # 如果按钮已初始化，则使用按钮状态
    is_micro_view = self.center_panel.micro_view_btn.isChecked()
    # 但如果两个按钮都未选中（初始状态），强制使用微观视图
    if (hasattr(self.center_panel, 'macro_view_btn') and 
        not self.center_panel.macro_view_btn.isChecked() and 
        not self.center_panel.micro_view_btn.isChecked()):
        is_micro_view = True
        # 同时更新按钮状态
        self.center_panel.micro_view_btn.setChecked(True)
        self.center_panel.macro_view_btn.setChecked(False)
```

### 2. 修复检测顺序（文件：`src/pages/shared/components/snake_path/snake_path_renderer.py`）

```python
# 修改前：
side = 'A' if hole.center_y > 0 else 'B'

# 修改后：
# 注意：在Qt坐标系中，y向下增长，所以y<0在屏幕上方
# 根据实际管板布局，上半部分是A侧，下半部分是B侧
side = 'A' if hole.center_y < 0 else 'B'  # Qt坐标系：y<0在上方为A侧
```

## 坐标系说明

### Qt坐标系（程序使用）
```
        y轴
        ↓
    ────┼──── → x轴
        │
   y<0  │  屏幕上方（A侧）
   ─────┼─────
   y>0  │  屏幕下方（B侧）
        │
```

### 物理坐标系（编号系统）
```
   y>0  │  A侧（上半部分）
   ─────┼─────
   y<0  │  B侧（下半部分）
        │
    ────┼──── → x轴
        ↑
        y轴
```

## 测试验证

### 1. 默认视图测试
- [x] 启动程序
- [x] 加载DXF文件
- [x] 验证是否自动显示微观视图（扇形放大）
- [x] 确认微观视图按钮为选中状态

### 2. 检测顺序测试
- [x] 开始检测流程
- [x] 验证第一个检测孔位是否为AC098R164（A区）
- [x] 观察检测路径是否遵循：
  - A侧（上半部分）→ B侧（下半部分）
  - 每侧内按列蛇形扫描

## 影响范围

1. **视图显示**：仅影响初始加载时的默认视图，不影响手动切换功能
2. **检测顺序**：影响所有使用蛇形路径的检测流程
3. **兼容性**：修复后与现有数据和功能完全兼容

## 注意事项

1. 修复基于Qt坐标系（Y轴向下）实现
2. A/B侧判定现在正确对应物理位置：
   - A侧 = 屏幕上方 = Qt坐标系 y<0
   - B侧 = 屏幕下方 = Qt坐标系 y>0
3. 此修复不影响已有的编号系统（AC/BC前缀）

## 后续建议

1. 考虑在代码中添加更多坐标系说明注释
2. 统一项目中的坐标系使用规范
3. 为关键坐标转换添加单元测试