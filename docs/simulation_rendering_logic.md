# 模拟渲染函数逻辑分析

## 概述

项目中的模拟渲染主要包含两个方面：
1. **DXF渲染** - 将DXF文件渲染为图像和带编号的可视化
2. **检测进度模拟** - 模拟孔位检测过程的动态可视化

## 1. DXF渲染系统

### 主要组件：`DXFRenderer` (src/modules/dxf_renderer.py)

#### 核心渲染流程
```python
def render_dxf_with_numbering(self, dxf_file_path: str, 
                            numbering_strategy: str = 'default',
                            output_path: Optional[str] = None) -> DXFRenderResult:
```

**4步渲染流程**:

##### 步骤1: DXF文件解析
```python
# 使用 ezdxf 库解析DXF文件
analysis_result = self.dxf_importer.import_from_dxf(dxf_file_path)

# 提取信息:
# - 孔位信息 (center_x, center_y, diameter)
# - 边界信息 (boundary_type, dimensions)
# - 元数据 (entity_count, version)
```

##### 步骤2: 孔位编号标注
```python
def _create_hole_annotations(self, holes: List[DXFHoleInfo], strategy: str):
    for i, hole in enumerate(holes):
        # 计算标注位置 (孔的右上方)
        label_offset_x = hole.diameter * 0.6
        label_offset_y = hole.diameter * 0.6
        
        # 生成编号标签 (C{col}R{row}格式)
        holes_per_row = max(1, int(math.sqrt(len(holes))))
        approx_row = (i // holes_per_row) + 1
        approx_col = (i % holes_per_row) + 1
        label = f"C{approx_col:03d}R{approx_row:03d}"
```

##### 步骤3: 图像渲染
```python
def _render_to_image(self, analysis_result, annotations, output_path):
    # 使用matplotlib创建图形
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # 渲染组件:
    # 1. 边界绘制 (如果存在)
    if boundary_info['has_boundary']:
        boundary_circle = Circle(center, radius, fill=False, color='gray')
        ax.add_patch(boundary_circle)
    
    # 2. 孔位绘制
    for annotation in annotations:
        # 绘制孔位圆圈
        hole_circle = Circle((x, y), diameter/2, fill=False, color='blue')
        ax.add_patch(hole_circle)
        
        # 绘制中心点
        ax.plot(x, y, 'bo', markersize=3)
        
        # 绘制编号标注
        ax.annotate(label, xy=(x, y), xytext=label_position,
                   bbox=dict(boxstyle="round", facecolor='yellow'),
                   arrowprops=dict(arrowstyle='->', color='red'))
    
    # 3. 保存高分辨率图像
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
```

##### 步骤4: 数据表生成
```python
def _generate_hole_table(self, annotations):
    for annotation in annotations:
        row = {
            '编号': annotation.label,
            'X坐标(mm)': hole.center_x,
            'Y坐标(mm)': hole.center_y,
            '直径(mm)': hole.diameter,
            '孔类型': hole.hole_type
        }
```

### 性能优化特点
- **分步时间统计**: 每个步骤都有详细的耗时记录
- **内存管理**: 使用非GUI后端(`matplotlib.use('Agg')`)
- **批量处理**: 一次性处理所有孔位
- **缓存清理**: 及时关闭matplotlib图形释放内存

## 2. 3D孔位渲染系统

### 主要组件：`Hole3DRenderer` (src/modules/hole_3d_renderer.py)

#### 3D渲染核心逻辑
```python
class Hole3DRenderer(FigureCanvas):
    def __init__(self):
        # 创建3D子图
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # 应用深色主题
        self.apply_dark_theme()
        
        # 设置鼠标交互
        self.setup_mouse_interaction()
```

#### 鼠标交互渲染
```python
def on_scroll(self, event):
    """鼠标滚轮缩放渲染"""
    # 获取当前坐标轴范围
    cur_xlim = self.ax.get_xlim()
    cur_ylim = self.ax.get_ylim() 
    cur_zlim = self.ax.get_zlim()
    
    # 计算缩放因子
    scale_factor = 0.9 if event.button == 'up' else 1.1
    
    # 以中心点为基准缩放
    x_center = (cur_xlim[0] + cur_xlim[1]) / 2
    # ... 计算新的坐标范围
    
    # 实时更新显示
    self.ax.set_xlim(x_center - x_range, x_center + x_range)
    self.draw()  # 触发重新渲染
```

#### 深色主题渲染
```python
def apply_dark_theme(self):
    """深色主题渲染设置"""
    # 背景色设置
    self.figure.patch.set_facecolor('#2C313C')
    self.ax.set_facecolor('#2C313C')
    
    # 坐标轴面板半透明效果
    self.ax.xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
    self.ax.yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
    self.ax.zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
```

## 3. 检测进度模拟渲染

### 主要组件：MainWindow中的模拟进度系统

#### 蛇形路径模拟渲染核心逻辑

##### 启动模拟
```python
def _start_simulation_progress_v2(self):
    """🐍 蛇形路径模拟进度"""
    
    # 1. 数据准备
    if not self.hole_collection:
        # 自动加载测试数据
        dxf_path = "/path/to/test.dxf"
        self.load_dxf_file(dxf_path)
    
    # 2. 蛇形路径算法排序
    all_holes = list(self.hole_collection.holes.values())
    self.snake_sorted_holes, self.snake_analysis = self._create_advanced_snake_path_with_analysis(
        all_holes, enable_dual_processing=True
    )
    
    # 3. 初始化模拟状态
    self.simulation_running_v2 = True
    self.snake_simulation_index = 0
    self.snake_stats = {"合格": 0, "异常": 0, "盲孔": 0, "拉杆孔": 0}
    
    # 4. 启动定时器
    self.snake_simulation_timer.start(10000)  # 10秒间隔
```

##### 动态状态渲染
```python
def _update_snake_simulation(self):
    """更新模拟渲染状态"""
    
    # 1. 双探头处理逻辑
    holes_to_process = []
    current_hole = self.snake_sorted_holes[self.snake_simulation_index]
    holes_to_process.append((current_hole, self.snake_simulation_index + 1))
    
    # 检查双探头模式
    probe2_index = self.snake_simulation_index + 1
    if probe2_index < len(self.snake_sorted_holes):
        probe2_hole = self.snake_sorted_holes[probe2_index]
        if current_hole.column == probe2_hole.column:
            holes_to_process.append((probe2_hole, probe2_index + 1))
    
    # 2. 视觉状态更新渲染
    current_view = self._get_current_graphics_view()
    
    for hole, index in holes_to_process:
        if hole.hole_id in current_view.hole_items:
            hole_item = current_view.hole_items[hole.hole_id]
            
            # 设置处理中状态 (蓝色渲染)
            hole.status = HoleStatus.PROCESSING
            hole_item.update_status(HoleStatus.PROCESSING)
            
            # 强制刷新渲染
            self._force_refresh_rendering(hole_item, current_view)
            
            # 延时设置最终状态
            QTimer.singleShot(9500, create_final_status_setter(hole, hole_item, current_view))
```

##### 强制刷新渲染机制
```python
def _force_refresh_rendering(self, hole_item, current_view):
    """强制刷新孔位渲染"""
    
    # 1. 项目级刷新
    hole_item.update()
    
    # 2. 场景级刷新
    if hasattr(current_view, 'scene'):
        scene_rect = hole_item.sceneBoundingRect()
        expanded_rect = scene_rect.adjusted(-5, -5, 5, 5)
        current_view.scene().update(expanded_rect)
        current_view.scene().invalidate(expanded_rect)
    
    # 3. 视口级刷新
    current_view.viewport().update()
    
    # 4. 全视口更新模式
    old_mode = current_view.viewportUpdateMode()
    current_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    current_view.viewport().repaint()
    current_view.setViewportUpdateMode(old_mode)
    
    # 5. 强制事件处理
    QApplication.processEvents()
```

##### 最终状态渲染逻辑
```python
def create_final_status_setter(hole, hole_item, view):
    def set_final_status():
        import random
        rand_value = random.random()
        
        # 状态概率分布
        if rand_value < 0.995:      # 99.5% - 合格
            final_status = HoleStatus.QUALIFIED
            color_emoji = "🟢"
        elif rand_value < 0.9999:   # 0.49% - 异常  
            final_status = HoleStatus.DEFECTIVE
            color_emoji = "🔴"
        else:                       # 0.01% - 其他
            final_status = random.choice([HoleStatus.BLIND, HoleStatus.TIE_ROD])
            color_emoji = "🟡" if final_status == HoleStatus.BLIND else "🔵"
        
        # 更新最终渲染状态
        hole.status = final_status
        hole_item.update_status(final_status)
        
        # 刷新渲染
        self._force_refresh_rendering(hole_item, view)
```

## 4. 渲染性能优化策略

### 时间控制
```python
# DXF渲染性能统计
total_time = time.time() - start_time
print(f"解析时间: {parse_time:.3f}s ({parse_time/total_time*100:.1f}%)")
print(f"标注时间: {annotation_time:.3f}s ({annotation_time/total_time*100:.1f}%)")
print(f"渲染时间: {render_time:.3f}s ({render_time/total_time*100:.1f}%)")

# 模拟渲染时序控制
simulation_timer.start(10000)  # 10秒/孔
processing_duration = 9500     # 9.5秒处理中状态
final_duration = 500          # 0.5秒最终状态
```

### 内存管理
```python
# matplotlib非GUI后端
matplotlib.use('Agg')

# 及时释放资源
plt.close()

# 强制事件处理防止内存泄露
QApplication.processEvents()
```

### 批量渲染优化
```python
# 双探头并行处理
if current_hole.column == probe2_hole.column:
    holes_to_process.append((probe2_hole, probe2_index + 1))

# 批量状态更新
for hole, index in holes_to_process:
    # 批量处理逻辑
```

## 5. 渲染数据流

```
用户操作 → 模拟启动
    ↓
蛇形路径算法排序 → 路径优化
    ↓  
定时器驱动 → 状态更新循环
    ↓
GraphicsView渲染 → 视觉状态变化
    ↓
强制刷新机制 → 实时显示更新
    ↓
最终状态设置 → 结果渲染
```

## 6. 关键渲染参数

### DXF渲染参数
- **图形尺寸**: 12×8英寸
- **分辨率**: 300 DPI
- **标注偏移**: diameter × 0.6
- **边距**: 50像素

### 3D渲染参数  
- **图形尺寸**: 14×12英寸
- **缩放因子**: 0.9/1.1
- **主题色**: #2C313C (深色)
- **透明度**: 0.4 (坐标轴面板)

### 模拟渲染参数
- **处理间隔**: 10秒/孔
- **处理中时长**: 9.5秒 (蓝色)
- **最终状态时长**: 0.5秒
- **状态概率**: 合格99.5%, 异常0.49%, 其他0.01%

## 7. 扩展建议

### 性能优化
1. **GPU加速**: 考虑使用WebGL或OpenGL后端
2. **虚拟化渲染**: 大数据集时只渲染可见区域
3. **预计算缓存**: 缓存常用的渲染结果

### 功能增强
1. **实时渲染**: WebSocket支持实时数据更新
2. **交互增强**: 支持拖拽、选择等交互操作
3. **导出选项**: 支持更多格式(SVG, PDF, 动画GIF)

### 代码结构优化
1. **渲染管线**: 建立统一的渲染管线架构
2. **插件系统**: 支持自定义渲染器插件
3. **配置管理**: 统一管理所有渲染参数