# 检测起始顺序修复说明

## 问题描述
检测仍然从BC099R001+BC103R001开始，而不是从BC098R164+BC102R164开始。

## 问题根源

### 1. 坐标系理解错误
在`src/pages/shared/components/snake_path/snake_path_renderer.py`文件的第419行，存在对Qt坐标系的理解错误：

- **Qt坐标系特点**：Y轴向下增长，Y值越小越在上方
- **R164位置**：在管板最上方，具有最小的Y值
- **R001位置**：靠近中心，具有较大的Y值

### 2. 排序逻辑错误
原代码：
```python
if sector_name in ['sector_1', 'sector_2']:
    # 上半部分：从最大Y开始（R164在顶部）
    sorted_rows = sorted(holes_by_y.keys(), reverse=True)
```

这个逻辑错误地使用了`reverse=True`，导致：
- 从最大Y值开始（实际上是最下方的行）
- 第一个处理的是R001而不是R164

### 3. 注释误导
原注释说"从最大Y开始（R164在顶部）"，但实际上R164在顶部时Y值是最小的，不是最大的。

## 修复方案

### 代码修改
已修改`src/pages/shared/components/snake_path/snake_path_renderer.py`第413-423行：

```python
# 按Y坐标排序所有行
# 根据用户要求：所有扇形都从R164开始
# 在Qt坐标系中，Y值越小越在上方
# 对于上半部分（sector_1和sector_2），R164在最上方（Y值最小）
# 对于下半部分（sector_3和sector_4），R164在最下方（Y值最大）
if sector_name in ['sector_1', 'sector_2']:
    # 上半部分：从最小Y开始（R164在顶部，Y值最小）
    sorted_rows = sorted(holes_by_y.keys())
else:
    # 下半部分：从最大Y开始（R164在底部，Y值最大）
    sorted_rows = sorted(holes_by_y.keys(), reverse=True)
```

## 修复效果

修复后的检测顺序：
1. **sector_1（右上）**：从R164开始，按S形路径扫描
2. **sector_2（左上）**：从R164开始，按S形路径扫描
3. **sector_3（左下）**：从R164开始（在底部），按S形路径扫描
4. **sector_4（右下）**：从R164开始（在底部），按S形路径扫描

这样确保了所有扇形都从R164行开始检测，符合用户需求。

## 验证方法

运行应用程序并开始模拟检测，观察：
1. 第一个检测单元应该包含R164行的孔位
2. 检测应该从管板的最外圈开始
3. 所有四个扇形都应该从各自的R164行开始

## 相关文件
- 修改文件：`src/pages/shared/components/snake_path/snake_path_renderer.py`
- 影响组件：`SimulationController`（使用snake_path_renderer生成检测单元）