# 优化视图模式设计总结

## 优化目标
1. 避免数据重复加载
2. 利用左侧小全景图进行扇形选择
3. 中间主视图专注于孔位显示

## 设计方案

### 视图分工
- **左侧小全景图**：扇形选择和导航
- **中间主视图**：
  - 宏观视图：显示整个管板所有孔位
  - 微观视图：显示选中扇形的孔位（通过显示/隐藏实现）

### 优化实现

#### 1. 移除数据重复加载
- 原来：点击扇形 → 创建新HoleCollection → `load_holes()` 清空并重新加载
- 现在：点击扇形 → 使用场景项过滤 → 显示/隐藏相应孔位

#### 2. 新增的方法
- `show_all_holes()`：显示所有孔位（宏观视图）
- `_show_sector_in_view()`：过滤显示扇形孔位（微观视图）

#### 3. 视图切换逻辑
```python
# 宏观视图
if mode == "macro":
    graphics_view.show_all_holes()  # 显示所有
    
# 微观视图  
else:  # micro
    _show_sector_in_view(current_sector)  # 过滤显示
```

#### 4. 初始加载优化
- 移除了默认选择扇形1的逻辑
- 让用户自主选择视图模式和扇形

## 优势
1. **性能提升**：避免重复创建图形项
2. **无闪烁**：使用显示/隐藏而非清空/加载
3. **平滑切换**：视图模式和扇形切换更流畅
4. **逻辑清晰**：数据加载与视图显示分离

## 文件修改
- `/src/pages/main_detection_p1/native_main_detection_view_p1.py`
  - 优化 `_on_view_mode_changed` 方法
  - 重写 `_on_panorama_sector_clicked` 方法
  - 新增 `_show_sector_in_view` 方法
  - 移除默认扇形选择
  
- `/src/core_business/graphics/graphics_view.py`
  - 新增 `show_all_holes` 方法