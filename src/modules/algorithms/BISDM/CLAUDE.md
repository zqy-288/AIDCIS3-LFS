# 工业内窥镜图像处理系统 - 项目记忆

## 项目概述

这是一个专业的工业内窥镜图像处理系统，用于处理管道内窥镜视频，生成管道内壁的高质量全景图像。系统支持离线批处理和实时在线处理两种模式。

## 项目结构

### 核心模块

1. **图像处理模块** (`image_processor/`)
   - `deblur.py`: 去模糊处理器 - 处理散焦模糊，支持Lucy-Richardson和维纳滤波
   - `unwrap.py`: 展开处理器 - 将圆形内窥镜图像展开为矩形
   - `stitch.py`: 拼接处理器 - 将多张展开图像拼接成全景图

2. **主程序**
   - `main.py`: 原始的离线批处理主程序
   - `main_realtime.py`: 新增的实时处理主程序
   - `realtime_processor.py`: 实时处理器核心类

3. **工具模块** (`utils/`)
   - `config.py`: 配置管理类，包含所有处理参数
   - `logger.py`: 日志配置

4. **辅助工具**
   - `video_frame_extractor.py`: 视频帧提取工具
   - `test.py`: 包含RTSCapture视频录制功能
   - `test_realtime.py`: 实时处理测试脚本
   - `demo_realtime.py`: 简单演示脚本

## 最新实现的功能（2025-01-19）

### 实时处理功能
1. **视频采集和录制**
   - 支持本地摄像头和网络流（RTSP/RTMP）
   - 同步录制原始视频
   - 使用RTSCapture类实现非阻塞视频读取

2. **实时关键帧选择**
   - 三种策略：固定间隔、相似度检测、运动检测
   - 减少处理负载，优化内存使用

3. **信号控制机制**
   - 交互式模式：键盘控制（S-开始，Q-停止）
   - 自动模式：定时或手动停止
   - 支持Ctrl+C安全退出

4. **视频显示修复**
   - 解决了线程冲突问题
   - 添加了线程安全的帧缓存机制
   - 改进了UI显示效果

## 关键技术特点

1. **图像处理算法**
   - Lucy-Richardson去卷积
   - 自适应直方图均衡化（CLAHE）
   - 多尺度特征匹配
   - 拉普拉斯金字塔融合

2. **性能优化**
   - 关键帧选择减少处理量
   - 多线程并行处理
   - 向量化计算（OpenCV remap）

3. **可视化增强**
   - 管道深度坐标轴
   - 展开角度标注（0-360度）
   - 实时状态显示

## 使用方法

### 离线处理
```bash
python main.py
```

### 实时处理
```bash
# 交互式模式
python main_realtime.py --mode interactive

# 自动模式（10秒）
python main_realtime.py --mode auto --duration 10

# 使用RTSP流
python main_realtime.py --source "rtsp://192.168.1.100:554/stream"
```

## 输出文件结构
```
output_realtime_YYYYMMDD_HHMMSS/
├── recorded_YYYYMMDD_HHMMSS.mp4  # 录制的原始视频
├── 00_keyframes/                  # 选中的关键帧
├── 01_deblurred/                  # 去模糊结果
├── 02_unwrapped/                  # 展开结果
├── panorama.png                   # 最终全景图
└── config.json                    # 使用的配置
```

## 待优化和扩展

1. **功能扩展**
   - 实现暂停/继续功能
   - 添加实时预览窗口显示处理结果
   - 支持流式拼接（边处理边拼接）
   - 添加进度条显示

2. **性能优化**
   - GPU加速支持
   - 多线程并行处理优化
   - 内存管理优化

3. **用户体验**
   - GUI界面
   - 参数实时调整
   - 处理结果实时预览

## 已知问题和解决方案

1. **视频窗口显示问题**（已解决）
   - 问题：直接访问rtscap导致线程冲突
   - 解决：添加display_frame缓存和线程锁

2. **内存占用**
   - 使用关键帧选择减少处理帧数
   - 定期清理缓存

## 重要配置参数

- `enable_keyframe_selection`: 启用关键帧选择
- `keyframe_strategy`: 选择策略（interval/similarity/motion）
- `defocus_method`: 去模糊方法（wiener/lucy_richardson）
- `circle_detection_method`: 圆检测方法（hough/adaptive）
- `save_intermediate`: 是否保存中间结果

## 开发注意事项

1. 图像处理使用浮点数提高精度
2. 所有模块都有完善的异常处理
3. 详细的日志记录便于调试
4. 配置驱动的参数调整

## 项目状态

- 基础功能：✅ 完成
- 实时处理：✅ 完成
- 视频显示：✅ 已修复
- GUI界面：⏳ 待开发
- GPU加速：⏳ 待开发

最后更新：2025-01-19