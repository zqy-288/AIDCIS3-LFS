# DynamicSectorDisplayRefactored 缩放功能流程图

## 流程图

```mermaid
graph TB
    %% 初始化阶段
    A[组件初始化] --> B[创建 OptimizedGraphicsView]
    B --> C{设置初始参数}
    C --> C1[disable_auto_fit = True]
    C --> C2[disable_auto_center = False]
    C --> C3[max_auto_scale = 1.5]

    %% 数据加载阶段
    D[数据加载触发] --> E[_process_hole_collection]
    E --> F[graphics_view.load_holes]
    F --> G[设置场景但不自动缩放]
    G --> H[隐藏所有孔位 setVisible False]
    H --> I[延迟200ms切换到扇形1]

    %% 扇形切换阶段
    J[switch_to_sector 触发] --> K{处理孔位可见性}
    K --> K1[显示当前扇形孔位]
    K --> K2[隐藏其他扇形孔位]
    K1 --> L[延迟50ms执行 delayed_fit]
    K2 --> L

    %% 缩放执行阶段
    L --> M{检查可用方法}
    M -->|存在| N[fit_to_visible_items]
    M -->|不存在| O[_calculate_visible_bounds]
    O --> P[计算可见孔位边界]
    P --> Q[添加10%边距]
    Q --> R[fitInView 保持比例]

    %% 用户交互
    S[用户键盘输入] --> T{快捷键类型}
    T -->|Ctrl + +| U[zoom_in]
    T -->|Ctrl + -| V[zoom_out]
    T -->|Ctrl + 0| W[reset_zoom]
    T -->|F键| X[fit_in_view_all]
    
    U --> Y[NavigationMixin处理]
    V --> Y
    W --> Y
    X --> Y
    Y --> Z[更新视图变换]

    %% 样式定义
    classDef init fill:#E8F4FD,stroke:#1976D2,stroke-width:2px
    classDef data fill:#FFF4E6,stroke:#F57C00,stroke-width:2px
    classDef switch fill:#E8F5E9,stroke:#388E3C,stroke-width:2px
    classDef core fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px
    classDef user fill:#FCE4EC,stroke:#C2185B,stroke-width:2px

    class A,B,C,C1,C2,C3 init
    class D,E,F,G,H,I data
    class J,K,K1,K2,L switch
    class M,N,O,P,Q,R core
    class S,T,U,V,W,X,Y,Z user
```

## 关键流程说明

### 1. 初始化阶段
- **目的**：防止加载时的自动缩放跳变
- **关键设置**：
  - `disable_auto_fit = True`：禁用自动适配
  - `max_auto_scale = 1.5`：限制最大自动缩放比例

### 2. 数据加载阶段
- **流程**：
  1. 数据通过 `_process_hole_collection` 处理
  2. 调用 `graphics_view.load_holes()` 加载孔位
  3. 所有孔位初始设置为隐藏
  4. 延迟200ms后自动切换到扇形1

### 3. 扇形切换阶段
- **流程**：
  1. 根据扇形数据设置孔位可见性
  2. 延迟50ms执行视图适配
  3. 计算可见孔位的边界
  4. 添加边距后执行缩放

### 4. 缩放计算
- **边界计算**：
  ```python
  # 计算所有可见孔位的边界
  visible_bounds = self._calculate_visible_bounds()
  
  # 添加10%边距
  margin_factor = 1.1
  expanded_bounds = QRectF(
      visible_bounds.x() - visible_bounds.width() * (margin_factor - 1) / 2,
      visible_bounds.y() - visible_bounds.height() * (margin_factor - 1) / 2,
      visible_bounds.width() * margin_factor,
      visible_bounds.height() * margin_factor
  )
  ```

### 5. 用户交互
- **支持的快捷键**：
  - `Ctrl + +`：放大
  - `Ctrl + -`：缩小  
  - `Ctrl + 0`：重置缩放
  - `F`：适应视图

## 缩放限制

| 参数 | 值 | 说明 |
|------|-----|------|
| min_zoom | 0.01 | 最小缩放比例 |
| max_zoom | 100.0 | 最大缩放比例 |
| max_auto_scale | 1.5 | 自动缩放最大比例 |
| zoom_factor_in | 1.25 | 放大因子 |
| zoom_factor_out | 0.8 | 缩小因子 |

## 性能优化措施

1. **延迟执行**：使用 `QTimer.singleShot` 避免频繁更新
2. **最小更新模式**：`QGraphicsView.MinimalViewportUpdate`
3. **禁用抗锯齿**：提升大量孔位时的渲染性能
4. **批量处理**：切换扇形时批量更新可见性

## 问题解决

1. **"先变大后适应"问题**
   - 通过 `disable_auto_fit = True` 解决
   - 使用延迟执行避免立即缩放

2. **延迟加载显示问题**
   - 数据加载后自动切换到扇形1
   - 确保有内容显示

3. **Mac兼容性**
   - 禁用鼠标滚轮缩放
   - 使用键盘快捷键替代