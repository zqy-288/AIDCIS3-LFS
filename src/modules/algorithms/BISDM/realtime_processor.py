#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时视频处理器
整合视频采集、录制和图像处理功能，实现实时全景图生成
"""

import threading
import cv2
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from collections import deque
import time
from typing import Optional, Tuple, List

from image_processor.deblur import DeblurProcessor
from image_processor.unwrap import UnwrapProcessor
from image_processor.stitch import StitchProcessor
from utils.config import Config


class RTSCapture(cv2.VideoCapture):
    """Real Time Streaming Capture.
    这个类必须使用 RTSCapture.create 方法创建，请不要直接实例化
    """

    _cur_frame = None
    _reading = False
    schemes = ["rtsp://", "rtmp://"]  # 用于识别实时流

    @staticmethod
    def create(url, *schemes):
        """实例化&初始化
        rtscap = RTSCapture.create("rtsp://example.com/live/1")
        or
        rtscap = RTSCapture.create("http://example.com/live/1.m3u8", "http://")
        """
        rtscap = RTSCapture(url)
        rtscap.frame_receiver = threading.Thread(target=rtscap.recv_frame, daemon=True)
        rtscap.schemes.extend(schemes)
        if isinstance(url, str) and url.startswith(tuple(rtscap.schemes)):
            rtscap._reading = True
        elif isinstance(url, int):
            # 这里可能是本机设备
            pass

        return rtscap

    def isStarted(self):
        """替代 VideoCapture.isOpened() """
        ok = self.isOpened()
        if ok and self._reading:
            ok = self.frame_receiver.is_alive()
        return ok

    def recv_frame(self):
        """子线程读取最新视频帧方法"""
        while self._reading and self.isOpened():
            ok, frame = self.read()
            if not ok: break
            self._cur_frame = frame
        self._reading = False

    def read2(self):
        """读取最新视频帧
        返回结果格式与 VideoCapture.read() 一样
        """
        frame = self._cur_frame
        self._cur_frame = None
        return frame is not None, frame

    def start_read(self):
        """启动子线程读取视频帧"""
        self.frame_receiver.start()
        self.read_latest_frame = self.read2 if self._reading else self.read

    def stop_read(self):
        """退出子线程方法"""
        self._reading = False
        if self.frame_receiver.is_alive(): self.frame_receiver.join()


class RealtimeProcessor:
    """实时视频处理器"""
    
    def __init__(self, capture_source, output_dir: str, config: Config):
        """
        初始化实时处理器
        
        Args:
            capture_source: 视频源（摄像头索引或视频流URL）
            output_dir: 输出目录
            config: 配置对象
        """
        self.capture_source = capture_source
        self.output_dir = Path(output_dir)
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建各阶段结果保存目录
        if config.save_intermediate:
            self.keyframes_dir = self.output_dir / "00_keyframes"
            self.deblurred_dir = self.output_dir / "01_deblurred"
            self.unwrapped_dir = self.output_dir / "02_unwrapped"
            self.keyframes_dir.mkdir(exist_ok=True)
            self.deblurred_dir.mkdir(exist_ok=True)
            self.unwrapped_dir.mkdir(exist_ok=True)
        
        # 视频采集和录制相关
        self.rtscap = None
        self.video_writer = None
        self.is_recording = False
        self.is_processing = False
        
        # 帧计数和时间
        self.frame_count = 0
        self.keyframe_count = 0
        self.start_time = None
        self.fps = 30  # 默认FPS
        
        # 关键帧选择相关
        self.last_keyframe = None
        self.last_keyframe_time = 0
        self.frame_buffer = deque(maxlen=10)  # 用于相似度和运动检测
        
        # 图像处理器
        self.deblur_processor = DeblurProcessor(config)
        self.unwrap_processor = UnwrapProcessor(config)
        self.stitch_processor = StitchProcessor(config)
        
        # 处理结果缓存
        self.processed_frames = []
        self.unwrapped_frames = []
        
        # 线程控制
        self.processing_thread = None
        self.processing_lock = threading.Lock()
        
        # 当前帧缓存（用于显示）
        self.current_display_frame = None
        self.display_lock = threading.Lock()
        
    def start_capture(self) -> bool:
        """启动视频采集"""
        try:
            self.rtscap = RTSCapture.create(self.capture_source)
            if not self.rtscap.isOpened():
                self.logger.error("无法打开视频源")
                return False
            
            # 获取视频属性
            self.fps = int(self.rtscap.get(cv2.CAP_PROP_FPS)) or 30
            width = int(self.rtscap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.rtscap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.logger.info(f"视频源已打开: {width}x{height} @ {self.fps}fps")
            
            # 启动帧接收
            self.rtscap.start_read()
            self.start_time = time.time()
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动视频采集失败: {str(e)}")
            return False
    
    def start_recording(self) -> bool:
        """开始录制视频"""
        if self.is_recording:
            self.logger.warning("视频已在录制中")
            return True
            
        try:
            # 获取视频属性
            width = int(self.rtscap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.rtscap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 生成视频文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = self.output_dir / f"recorded_{timestamp}.mp4"
            
            # 初始化视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                str(video_filename), fourcc, self.fps, (width, height)
            )
            
            if not self.video_writer.isOpened():
                self.logger.error("无法创建视频写入器")
                return False
                
            self.is_recording = True
            self.logger.info(f"开始录制视频: {video_filename}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"开始录制失败: {str(e)}")
            return False
    
    def stop_recording(self):
        """停止录制视频"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        self.logger.info(f"视频录制已停止，共录制 {self.frame_count} 帧")
    
    def stop_capture(self):
        """停止视频采集"""
        if self.rtscap:
            self.rtscap.stop_read()
            self.rtscap.release()
            self.rtscap = None
            
        self.logger.info("视频采集已停止")
    
    def should_select_keyframe(self, frame: np.ndarray) -> bool:
        """
        判断当前帧是否应该被选为关键帧
        
        Args:
            frame: 当前帧
            
        Returns:
            是否选择为关键帧
        """
        if not self.config.enable_keyframe_selection:
            return True  # 不启用关键帧选择，处理所有帧
            
        current_time = time.time() - self.start_time
        
        if self.config.keyframe_strategy == "interval":
            # 固定间隔策略
            frame_interval = 1.0 / self.fps * self.config.keyframe_interval
            if current_time - self.last_keyframe_time >= frame_interval:
                self.last_keyframe_time = current_time
                return True
                
        elif self.config.keyframe_strategy == "similarity":
            # 相似度策略
            if self.last_keyframe is None:
                self.last_keyframe = frame
                self.last_keyframe_time = current_time
                return True
                
            # 计算相似度
            similarity = self._calculate_similarity(self.last_keyframe, frame)
            if similarity < (1.0 - self.config.similarity_threshold):
                self.last_keyframe = frame
                self.last_keyframe_time = current_time
                return True
                
        elif self.config.keyframe_strategy == "motion":
            # 运动检测策略
            if self.last_keyframe is None:
                self.last_keyframe = frame
                self.last_keyframe_time = current_time
                return True
                
            # 计算运动量
            motion = self._calculate_motion(self.last_keyframe, frame)
            if motion > self.config.motion_threshold:
                self.last_keyframe = frame
                self.last_keyframe_time = current_time
                return True
        
        return False
    
    def _calculate_similarity(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算两帧之间的相似度"""
        # 转换为灰度图
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) if len(frame1.shape) == 3 else frame1
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY) if len(frame2.shape) == 3 else frame2
        
        # 计算直方图
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        
        # 计算相关性
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return correlation
    
    def _calculate_motion(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算两帧之间的运动量"""
        # 转换为灰度图
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) if len(frame1.shape) == 3 else frame1
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY) if len(frame2.shape) == 3 else frame2
        
        # 使用帧差计算运动量
        diff = cv2.absdiff(gray1, gray2)
        motion_magnitude = np.mean(diff) / 255.0
        return motion_magnitude
    
    def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        处理单帧图像
        
        Args:
            frame: 输入帧
            
        Returns:
            处理后的帧（如果被选为关键帧）
        """
        try:
            # 检查是否应该选择为关键帧
            if not self.should_select_keyframe(frame):
                return None
            
            self.logger.info(f"选择关键帧 {self.keyframe_count}")
            
            # 保存原始关键帧
            if self.config.save_intermediate:
                keyframe_path = self.keyframes_dir / f"keyframe_{self.keyframe_count:04d}.png"
                cv2.imwrite(str(keyframe_path), frame)
            
            # 1. 去模糊处理
            enhanced = self.deblur_processor.process(frame, self.keyframe_count, self.output_dir)
            
            # 保存增强结果
            if self.config.save_intermediate:
                enhanced_path = self.deblurred_dir / f"enhanced_{self.keyframe_count:04d}.png"
                cv2.imwrite(str(enhanced_path), enhanced)
            
            # 存储处理后的帧
            self.processed_frames.append(enhanced)
            self.keyframe_count += 1
            
            return enhanced
            
        except Exception as e:
            self.logger.error(f"处理帧时出错: {str(e)}")
            return None
    
    def process_unwrap_and_stitch(self):
        """处理展开和拼接（在处理结束时调用）"""
        if not self.processed_frames:
            self.logger.warning("没有处理的帧，跳过展开和拼接")
            return None
            
        try:
            # 2. 批量展开处理
            self.logger.info(f"开始展开 {len(self.processed_frames)} 张图像")
            self.unwrapped_frames = self.unwrap_processor.process(
                self.processed_frames, self.output_dir
            )
            
            # 3. 图像拼接
            self.logger.info(f"开始拼接 {len(self.unwrapped_frames)} 张展开图像")
            panorama = self.stitch_processor.process(
                self.unwrapped_frames, self.output_dir
            )
            
            return panorama
            
        except Exception as e:
            self.logger.error(f"展开和拼接处理失败: {str(e)}")
            return None
    
    def run(self):
        """主运行循环"""
        self.is_processing = True
        
        try:
            while self.is_processing and self.rtscap.isStarted():
                # 获取最新帧
                ok, frame = self.rtscap.read_latest_frame()
                if not ok or frame is None:
                    continue
                
                # 更新显示帧
                with self.display_lock:
                    self.current_display_frame = frame.copy()
                
                # 录制原始视频
                if self.is_recording and self.video_writer:
                    self.video_writer.write(frame)
                
                # 处理帧
                self.process_frame(frame)
                
                self.frame_count += 1
                
                # 显示进度（可选）
                if self.frame_count % 30 == 0:  # 每秒更新一次
                    self.logger.info(f"已处理 {self.frame_count} 帧, 选择了 {self.keyframe_count} 个关键帧")
                    
        except Exception as e:
            self.logger.error(f"处理循环出错: {str(e)}")
        finally:
            self.is_processing = False
    
    def start_processing(self):
        """开始处理（在新线程中）"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.logger.warning("处理已在进行中")
            return
            
        self.processing_thread = threading.Thread(target=self.run, daemon=True)
        self.processing_thread.start()
    
    def stop_processing(self) -> Optional[np.ndarray]:
        """
        停止处理并返回最终结果
        
        Returns:
            全景图结果
        """
        self.is_processing = False
        
        # 等待处理线程结束
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        # 停止录制和采集
        self.stop_recording()
        self.stop_capture()
        
        # 执行最终的展开和拼接
        panorama = self.process_unwrap_and_stitch()
        
        if panorama is not None:
            # 保存最终结果
            output_file = self.output_dir / f"panorama.{self.config.output_format}"
            cv2.imwrite(str(output_file), panorama)
            self.logger.info(f"全景图已保存至: {output_file}")
            
            # 保存配置文件
            self.config.save_json(str(self.output_dir / "config.json"))
        
        return panorama
    
    def get_status(self) -> dict:
        """获取当前处理状态"""
        return {
            'is_recording': self.is_recording,
            'is_processing': self.is_processing,
            'frame_count': self.frame_count,
            'keyframe_count': self.keyframe_count,
            'processed_frames': len(self.processed_frames),
            'fps': self.fps
        }
    
    def get_display_frame(self) -> Optional[np.ndarray]:
        """获取用于显示的当前帧"""
        with self.display_lock:
            if self.current_display_frame is not None:
                return self.current_display_frame.copy()
        return None