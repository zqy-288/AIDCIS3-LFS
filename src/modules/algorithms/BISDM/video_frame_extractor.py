#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频切帧提取器
从视频文件中提取指定时间段的帧并保存为图像
"""

import cv2
import os
import numpy as np
from pathlib import Path
import argparse
from datetime import timedelta


class VideoFrameExtractor:
    """视频帧提取器"""
    
    def __init__(self, video_path: str, output_dir: str = "extracted_frames"):
        """
        初始化视频帧提取器
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
        """
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)
        
        # 检查视频文件是否存在
        if not self.video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 打开视频
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps
        
        print(f"视频信息:")
        print(f"  文件: {self.video_path.name}")
        print(f"  FPS: {self.fps:.2f}")
        print(f"  总帧数: {self.total_frames}")
        print(f"  时长: {self.format_time(self.duration)}")
    
    def format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        return str(timedelta(seconds=int(seconds)))
    
    def extract_frames(self, start_time: float, end_time: float, 
                      frame_prefix: str = "frame", 
                      image_format: str = "jpg",
                      save_every_nth: int = 1) -> int:
        """
        提取指定时间段的帧
        
        Args:
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            frame_prefix: 帧文件名前缀
            image_format: 图像格式 (jpg, png)
            save_every_nth: 每N帧保存一次（1表示所有帧）
            
        Returns:
            提取的帧数
        """
        # 参数验证
        if start_time < 0:
            start_time = 0
        if end_time > self.duration:
            end_time = self.duration
        if start_time >= end_time:
            raise ValueError(f"开始时间({start_time}s)必须小于结束时间({end_time}s)")
        
        print(f"\n开始提取帧:")
        print(f"  时间段: {self.format_time(start_time)} - {self.format_time(end_time)}")
        print(f"  输出目录: {self.output_dir}")
        print(f"  图像格式: {image_format}")
        print(f"  保存频率: 每{save_every_nth}帧")
        
        # 计算起始和结束帧号
        start_frame = int(start_time * self.fps)
        end_frame = int(end_time * self.fps)
        
        # 设置视频位置到开始帧
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        extracted_count = 0
        frame_count = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if current_frame > end_frame:
                break
            
            # 只保存指定频率的帧
            if frame_count % save_every_nth == 0:
                # 计算当前时间
                current_time = current_frame / self.fps
                
                # 生成文件名
                timestamp = f"{current_time:.3f}s"
                filename = f"{frame_prefix}_{extracted_count:04d}_{timestamp}.{image_format}"
                filepath = self.output_dir / filename
                
                # 保存图像
                success = cv2.imwrite(str(filepath), frame)
                if success:
                    extracted_count += 1
                    if extracted_count == 1 or extracted_count % 10 == 0:
                        print(f"  已提取: {extracted_count} 帧 (当前时间: {timestamp})")
                else:
                    print(f"  警告: 保存失败 - {filename}")
            
            frame_count += 1
        
        print(f"\n提取完成!")
        print(f"  总共提取: {extracted_count} 帧")
        print(f"  保存位置: {self.output_dir.absolute()}")
        
        return extracted_count
    
    def get_frame_at_time(self, time_seconds: float) -> np.ndarray:
        """获取指定时间的单帧"""
        frame_number = int(time_seconds * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            raise ValueError(f"无法获取时间 {time_seconds}s 处的帧")
    
    def save_preview_frame(self, time_seconds: float) -> str:
        """保存预览帧"""
        frame = self.get_frame_at_time(time_seconds)
        preview_path = self.output_dir / f"preview_{time_seconds}s.jpg"
        cv2.imwrite(str(preview_path), frame)
        return str(preview_path)
    
    def __del__(self):
        """析构函数，释放资源"""
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()


def main():
    """主函数"""
    # 设置参数
    video_path = "/Users/yangziteng/Documents/project/project_v1/60fps.mp4"
    start_time = 1.0  # 2秒开始
    end_time = 2.0    # 7秒结束
    output_dir = "extracted_frames_60fps"
    
    try:
        # 创建提取器
        extractor = VideoFrameExtractor(video_path, output_dir)
        
        # 保存预览帧
        print("保存预览帧...")
        preview_start = extractor.save_preview_frame(start_time)
        preview_end = extractor.save_preview_frame(end_time)
        print(f"  开始帧预览: {preview_start}")
        print(f"  结束帧预览: {preview_end}")
        
        # 提取帧（每帧都保存）
        extracted_count = extractor.extract_frames(
            start_time=start_time,
            end_time=end_time,
            frame_prefix="final_frame",
            image_format="jpg",
            save_every_nth=1  # 保存所有帧
        )
        
        print(f"\n✅ 成功提取了 {extracted_count} 帧图像")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # 支持命令行参数
    parser = argparse.ArgumentParser(description="视频帧提取器")
    parser.add_argument("--video", "-v", default="/Users/yangziteng/Documents/project/project_v1/60fps.mp4",
                       help="视频文件路径")
    parser.add_argument("--start", "-s", type=float, default=1.0,
                       help="开始时间（秒）")
    parser.add_argument("--end", "-e", type=float, default=2.0,
                       help="结束时间（秒）")
    parser.add_argument("--output", "-o", default="extracted_frames_60fps",
                       help="输出目录")
    parser.add_argument("--format", "-f", default="jpg", choices=["jpg", "png"],
                       help="图像格式")
    parser.add_argument("--every", type=int, default=2,
                       help="每N帧保存一次")
    
    args = parser.parse_args()
    
    try:
        extractor = VideoFrameExtractor(args.video, args.output)
        
        # 保存预览帧
        print("保存预览帧...")
        preview_start = extractor.save_preview_frame(args.start)
        preview_end = extractor.save_preview_frame(args.end)
        print(f"  开始帧预览: {preview_start}")
        print(f"  结束帧预览: {preview_end}")
        
        # 提取帧
        extracted_count = extractor.extract_frames(
            start_time=args.start,
            end_time=args.end,
            frame_prefix="frame",
            image_format=args.format,
            save_every_nth=args.every
        )
        
        print(f"\n✅ 成功提取了 {extracted_count} 帧图像")
        
    except Exception as e:
        print(f"❌ 错误: {e}") 