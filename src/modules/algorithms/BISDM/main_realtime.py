#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时内窥镜图像处理系统主程序
支持实时视频采集、关键帧选择和全景图生成
"""

import cv2
import logging
import sys
import signal
import threading
from pathlib import Path
from datetime import datetime
import numpy as np
from realtime_processor import RealtimeProcessor
from utils.logger import setup_logger
from utils.config import Config


class RealtimeEndoscopeSystem:
    """实时内窥镜处理系统"""
    
    def __init__(self, capture_source, config: Config):
        """
        初始化系统
        
        Args:
            capture_source: 视频源（摄像头索引或视频流URL）
            config: 配置对象
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.capture_source = capture_source
        
        # 生成带时间戳的输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"output_realtime_{timestamp}"
        
        # 创建实时处理器
        self.processor = RealtimeProcessor(capture_source, self.output_dir, config)
        
        # 系统状态
        self.is_running = False
        self.is_processing = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """处理系统信号"""
        self.logger.info("接收到停止信号，正在安全退出...")
        self.stop()
        sys.exit(0)
    
    def start(self) -> bool:
        """
        开始处理（接收开始信号）
        启动视频采集、录制和处理
        """
        self.logger.info("=" * 60)
        self.logger.info("实时内窥镜图像处理系统启动")
        self.logger.info("=" * 60)
        
        # 显示配置信息
        self.logger.info(self.config.get_processing_summary())
        
        # 启动视频采集
        if not self.processor.start_capture():
            self.logger.error("启动视频采集失败")
            return False
        
        # 启动视频录制
        if not self.processor.start_recording():
            self.logger.error("启动视频录制失败")
            return False
        
        # 启动处理线程
        self.processor.start_processing()
        
        self.is_running = True
        self.is_processing = True
        
        self.logger.info("系统已启动，正在处理...")
        self.logger.info("按 Ctrl+C 或发送停止信号结束处理")
        
        return True
    
    def stop(self):
        """
        停止处理（接收结束信号）
        停止采集、保存结果并输出
        """
        if not self.is_running:
            return
            
        self.logger.info("正在停止处理...")
        self.is_processing = False
        
        # 停止处理并获取结果
        panorama = self.processor.stop_processing()
        
        # 获取最终状态
        status = self.processor.get_status()
        
        # 输出处理摘要
        self.logger.info("=" * 60)
        self.logger.info("处理完成，结果摘要:")
        self.logger.info(f"- 处理时长: {status['frame_count'] / status['fps']:.1f} 秒")
        self.logger.info(f"- 总帧数: {status['frame_count']}")
        self.logger.info(f"- 选择关键帧数: {status['keyframe_count']}")
        self.logger.info(f"- 成功处理帧数: {status['processed_frames']}")
        self.logger.info(f"- 输出目录: {self.output_dir}")
        
        if panorama is not None:
            self.logger.info(f"- 全景图尺寸: {panorama.shape}")
            self.logger.info(f"- 全景图文件: {self.output_dir}/panorama.{self.config.output_format}")
        
        self.logger.info("=" * 60)
        
        self.is_running = False
    
    def run_interactive(self):
        """
        交互式运行模式
        支持键盘控制开始/停止
        """
        print("\n=== 实时内窥镜处理系统 ===")
        print("控制命令:")
        print("  S - 开始处理")
        print("  Q - 停止并退出")
        print("  P - 暂停/继续（未实现）")
        print("========================\n")
        
        # 创建显示窗口
        cv2.namedWindow("Realtime Endoscope System", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Realtime Endoscope System", 800, 600)
        
        # 创建一个黑色背景作为初始显示
        blank_frame = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "Press 'S' to Start", (250, 300), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Realtime Endoscope System", blank_frame)
        
        while True:
            # 获取当前帧用于显示（如果正在处理）
            if self.is_processing and self.processor:
                frame = self.processor.get_display_frame()
                if frame is not None:
                    # 在帧上显示状态信息
                    status = self.processor.get_status()
                    
                    # 创建状态栏背景
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 80), (0, 0, 0), -1)
                    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
                    
                    # 显示状态信息
                    status_text1 = f"Recording: {'ON' if status['is_recording'] else 'OFF'} | FPS: {status['fps']}"
                    status_text2 = f"Frames: {status['frame_count']} | Keyframes: {status['keyframe_count']} | Processed: {status['processed_frames']}"
                    
                    cv2.putText(frame, status_text1, (10, 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, status_text2, (10, 55), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    # 显示控制提示
                    cv2.putText(frame, "Press 'Q' to stop", (frame.shape[1] - 200, 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    
                    # 显示帧
                    cv2.imshow("Realtime Endoscope System", frame)
                else:
                    # 如果没有帧，显示等待信息
                    wait_frame = np.zeros((600, 800, 3), dtype=np.uint8)
                    cv2.putText(wait_frame, "Waiting for frames...", (250, 300), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    cv2.imshow("Realtime Endoscope System", wait_frame)
            
            # 处理键盘输入
            key = cv2.waitKey(30) & 0xFF  # 增加等待时间以减少CPU占用
            
            if key == ord('s') or key == ord('S'):
                if not self.is_running:
                    print("开始处理...")
                    if self.start():
                        print("处理已开始")
                    else:
                        print("启动失败")
                else:
                    print("系统已在运行中")
                    
            elif key == ord('q') or key == ord('Q'):
                if self.is_running:
                    print("停止处理...")
                    self.stop()
                break
                
            elif key == ord('p') or key == ord('P'):
                print("暂停/继续功能尚未实现")
        
        cv2.destroyAllWindows()
    
    def run_auto(self, duration_seconds: float = None):
        """
        自动运行模式
        启动后自动处理指定时长
        
        Args:
            duration_seconds: 处理时长（秒），None表示手动停止
        """
        if not self.start():
            self.logger.error("启动失败")
            return
        
        if duration_seconds:
            self.logger.info(f"将在 {duration_seconds} 秒后自动停止")
            # 使用定时器自动停止
            timer = threading.Timer(duration_seconds, self.stop)
            timer.start()
            
            # 等待处理完成
            try:
                timer.join()
            except KeyboardInterrupt:
                timer.cancel()
                self.stop()
        else:
            # 等待手动停止
            try:
                while self.is_running:
                    threading.Event().wait(1)
            except KeyboardInterrupt:
                self.stop()


def main():
    """主函数"""
    # 设置日志
    setup_logger()
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = Config()
    
    # 验证配置
    config.validate()
    
    # 设置视频源
    # 可以是摄像头索引（0, 1, 2...）或视频流URL
    capture_source = 0  # 使用默认摄像头
    # capture_source = "rtsp://example.com/stream"  # RTSP流示例
    
    # 命令行参数解析
    import argparse
    parser = argparse.ArgumentParser(description="实时内窥镜图像处理系统")
    parser.add_argument("--source", "-s", default=0, 
                       help="视频源（摄像头索引或流URL）")
    parser.add_argument("--mode", "-m", choices=["interactive", "auto"], 
                       default="interactive",
                       help="运行模式：interactive（交互式）或auto（自动）")
    parser.add_argument("--duration", "-d", type=float, default=None,
                       help="自动模式下的处理时长（秒）")
    parser.add_argument("--config", "-c", type=str, default=None,
                       help="配置文件路径")
    
    args = parser.parse_args()
    
    # 解析视频源
    if args.source.isdigit():
        capture_source = int(args.source)
    else:
        capture_source = args.source
    
    # 加载自定义配置文件
    if args.config:
        config = Config.from_json(args.config)
        config.validate()
    
    try:
        # 创建系统实例
        system = RealtimeEndoscopeSystem(capture_source, config)
        
        # 根据模式运行
        if args.mode == "interactive":
            system.run_interactive()
        else:
            system.run_auto(args.duration)
            
    except Exception as e:
        logger.error(f"系统运行出错: {str(e)}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())