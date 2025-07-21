# 实时内窥镜图像处理系统使用指南

## 概述

实时处理系统可以从摄像头或视频流实时采集视频，自动选择关键帧进行处理，生成管道内壁全景图。

## 主要功能

1. **实时视频采集**：支持本地摄像头和网络视频流（RTSP/RTMP）
2. **同步视频录制**：保存原始视频供后续分析
3. **智能关键帧选择**：减少处理负载，提高效率
4. **实时图像处理**：去模糊增强、圆形展开、全景拼接
5. **信号控制**：支持开始/停止信号控制处理流程

## 使用方法

### 1. 交互式模式（推荐）

```bash
python main_realtime.py --mode interactive
```

控制命令：
- `S` - 开始处理
- `Q` - 停止并退出
- 显示窗口会实时显示处理状态

### 2. 自动模式

```bash
# 处理10秒后自动停止
python main_realtime.py --mode auto --duration 10

# 手动停止（Ctrl+C）
python main_realtime.py --mode auto
```

### 3. 指定视频源

```bash
# 使用摄像头1
python main_realtime.py --source 1

# 使用RTSP流
python main_realtime.py --source "rtsp://192.168.1.100:554/stream"
```

### 4. 使用自定义配置

```bash
python main_realtime.py --config custom_config.json
```

## 配置参数

主要配置参数（在 `utils/config.py` 中设置）：

### 关键帧选择
- `enable_keyframe_selection`: 是否启用关键帧选择
- `keyframe_strategy`: 选择策略
  - `"interval"`: 固定间隔
  - `"similarity"`: 基于相似度
  - `"motion"`: 基于运动检测
- `keyframe_interval`: 间隔帧数（interval策略）
- `similarity_threshold`: 相似度阈值（similarity策略）
- `motion_threshold`: 运动阈值（motion策略）

### 处理参数
- `defocus_method`: 去模糊方法（"wiener" 或 "lucy_richardson"）
- `circle_detection_method`: 圆检测方法（"hough" 或 "adaptive"）
- `save_intermediate`: 是否保存中间结果

## 输出文件

处理完成后，在 `output_realtime_YYYYMMDD_HHMMSS/` 目录下生成：

```
output_realtime_20250119_120000/
├── recorded_20250119_120000.mp4    # 录制的原始视频
├── 00_keyframes/                    # 选中的关键帧
│   ├── keyframe_0000.png
│   ├── keyframe_0001.png
│   └── ...
├── 01_deblurred/                    # 去模糊处理结果
│   └── ...
├── 02_unwrapped/                    # 展开处理结果
│   └── ...
├── panorama.png                     # 最终全景图
└── config.json                      # 使用的配置参数
```

## 测试功能

运行测试脚本验证功能：

```bash
python test_realtime.py
```

## 性能优化建议

1. **关键帧选择**：
   - 高质量需求：禁用关键帧选择或使用小间隔
   - 实时性需求：使用较大间隔（10-20帧）

2. **处理速度**：
   - 降低图像分辨率
   - 使用 "wiener" 去模糊方法
   - 减少形态学操作迭代次数

3. **内存管理**：
   - 启用关键帧选择
   - 限制最大关键帧数（`max_keyframes`）
   - 定期处理和清理缓存

## 常见问题

1. **摄像头无法打开**：
   - 检查摄像头索引是否正确
   - 确认摄像头未被其他程序占用

2. **处理速度慢**：
   - 启用关键帧选择
   - 调整关键帧间隔
   - 降低处理分辨率

3. **内存占用高**：
   - 减少 `max_keyframes` 值
   - 使用 "interval" 策略
   - 分段处理长视频

## 开发说明

### 核心类
- `RealtimeProcessor`: 实时处理器，整合所有功能
- `RealtimeEndoscopeSystem`: 系统控制类，处理信号和用户交互

### 处理流程
1. 接收开始信号 → `start()`
2. 启动视频采集 → `start_capture()`
3. 启动视频录制 → `start_recording()`
4. 处理循环 → `run()`
   - 获取帧 → `read_latest_frame()`
   - 关键帧选择 → `should_select_keyframe()`
   - 图像处理 → `process_frame()`
5. 接收停止信号 → `stop()`
6. 展开和拼接 → `process_unwrap_and_stitch()`
7. 保存结果

### 扩展功能
- 实现暂停/继续功能
- 添加实时预览窗口
- 支持多线程并行处理
- 实现流式拼接（边处理边拼接）