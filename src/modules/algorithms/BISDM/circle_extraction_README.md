# 圆形区域提取工具

这个工具用于从图像中提取圆形区域，特别是基于对比度清晰的圆形。工具使用OpenCV的HoughCircles算法检测圆形，并提取圆形区域。

## 功能特点

1. 自动检测图像中的圆形区域
2. 提取圆形区域并保存为单独的图像
3. 支持批量处理多个图像
4. 生成可视化结果，展示检测和提取过程
5. 保存圆形信息（中心坐标和半径）到CSV文件

## 使用方法

### 单个图像处理

```python
from test import extract_and_save_circle

# 处理单个图像
input_image = "path/to/your/image.png"
output_dir = "path/to/output/directory"
extract_and_save_circle(input_image, output_dir, min_radius=30, max_radius=200)
```

### 批量处理

```python
from test import batch_process_images

# 批量处理目录中的图像
input_dir = "path/to/input/directory"
output_dir = "path/to/output/directory"
batch_process_images(input_dir, output_dir, pattern="*.png", min_radius=30, max_radius=200)
```

## 参数说明

- `min_radius`: 最小圆半径（像素）
- `max_radius`: 最大圆半径（像素）
- `pattern`: 文件匹配模式，用于批量处理（例如："*.png"）

## 输出文件

工具会在指定的输出目录中生成以下文件：

1. `{image_name}_circle_marked.png`: 标记了检测到的圆形的原始图像
2. `{image_name}_circle_mask.png`: 应用了圆形掩码的图像
3. `{image_name}_circle_cropped.png`: 裁剪后的圆形区域
4. `{image_name}_enhanced.png`: 增强后的图像
5. `{image_name}_process.png`: 处理过程的可视化
6. `circles_data.csv`: 包含所有检测到的圆形信息的CSV文件（仅批量处理模式）

## 技术细节

工具使用以下步骤处理图像：

1. 读取图像并获取ROI（感兴趣区域）
2. 应用CLAHE（对比度受限的自适应直方图均衡化）增强图像对比度
3. 应用高斯模糊减少噪声
4. 使用HoughCircles算法检测圆形
5. 创建掩码并提取圆形区域
6. 裁剪到圆形区域的最小外接矩形
7. 保存结果和可视化处理过程

## 依赖库

- OpenCV
- NumPy
- Matplotlib
- scikit-learn (用于聚类去重) 