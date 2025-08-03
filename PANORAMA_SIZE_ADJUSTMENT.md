# 全景预览框尺寸调整

## 问题
用户反馈全景预览框太小，不便于查看管板的整体情况。需要同时放大预览框和其外部容器。

## 原始设置
- 在 `native_main_detection_view_p1.py` 中：
  - `setMinimumHeight(200)` - 最小高度仅200像素
  - 使用了 `Expanding` 策略，导致尺寸不固定
  - 左侧面板宽度：380px
  - 没有设置QGroupBox的最小高度

## 修改方案

### 1. 增大左侧面板宽度
```python
self.setFixedWidth(400)  # 从380px增加到400px
```

### 2. 设置全景预览组框最小高度
```python
group.setMinimumHeight(400)  # 确保组框有足够高度
```

### 3. 增大全景预览组件尺寸
```python
self.sidebar_panorama.setFixedSize(380, 380)  # 380x380的正方形
```

## 最终尺寸说明
- **左侧面板宽度**：400px（固定）
- **全景预览组框**：最小高度400px
- **全景预览组件**：380x380px（正方形）
- **边距**：左右各10px

## 效果
1. 全景预览框显著变大，更容易看清管板整体布局
2. 外部组框也相应增大，视觉效果更协调
3. 正方形设计更适合圆形管板的显示
4. 固定尺寸确保界面布局稳定

## 文件修改
- `/src/pages/main_detection_p1/native_main_detection_view_p1.py`
  - 第75行：左侧面板宽度从380px改为400px
  - 第265行：添加组框最小高度400px
  - 第276行：全景预览组件尺寸改为380x380px