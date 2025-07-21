#!/usr/local/bin/python3
# encoding: utf-8
# Video recorder script based on RTSCapture

import threading
import cv2
import sys
import os
from datetime import datetime


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


class VideoRecorder:
    """Video recording and frame capture class"""
    
    def __init__(self, capture_source):
        self.capture_source = capture_source
        self.rtscap = RTSCapture.create(capture_source)
        self.is_recording = False
        self.video_writer = None
        self.frame_count = 0
        self.captured_frames_count = 0
        
        # 创建输出目录
        self.output_dir = "recorded_videos"
        self.frames_dir = "captured_frames"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.frames_dir, exist_ok=True)
        
    def start_capture(self):
        """启动摄像头捕获"""
        if not self.rtscap.isOpened():
            print("Error: Cannot open capture device")
            return False
        
        self.rtscap.start_read()
        print("Camera capture started")
        return True
    
    def start_recording(self):
        """开始录制视频"""
        if self.is_recording:
            print("Recording is already in progress")
            return
            
        # 获取视频属性
        fps = int(self.rtscap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(self.rtscap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.rtscap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 生成视频文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = os.path.join(self.output_dir, f"video_{timestamp}.mp4")
        
        # 初始化视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(video_filename, fourcc, fps, (width, height))
        
        if not self.video_writer.isOpened():
            print("Error: Cannot create video writer")
            return
            
        self.is_recording = True
        self.frame_count = 0
        print(f"Recording started: {video_filename}")
        print(f"Video properties: {width}x{height} @ {fps}fps")
    
    def stop_recording(self):
        """停止录制视频"""
        if not self.is_recording:
            print("No recording in progress")
            return
            
        self.is_recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        print(f"Recording stopped. Total frames: {self.frame_count}")
    
    def capture_frame(self, frame):
        """捕获并保存当前帧"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
        frame_filename = os.path.join(self.frames_dir, f"frame_{timestamp}.jpg")
        
        if cv2.imwrite(frame_filename, frame):
            self.captured_frames_count += 1
            print(f"Frame captured: {frame_filename}")
        else:
            print("Error: Failed to save frame")
    
    def process_frame(self, frame):
        """处理视频帧"""
        if frame is None:
            return
            
        # 如果正在录制，写入视频文件
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)
            self.frame_count += 1
            
        # 在帧上显示录制状态
        status_text = "REC" if self.is_recording else "READY"
        color = (0, 0, 255) if self.is_recording else (0, 255, 0)
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # 显示帧计数信息
        info_text = f"Frames: {self.frame_count} | Captured: {self.captured_frames_count}"
        cv2.putText(frame, info_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def run(self):
        """主运行循环"""
        if not self.start_capture():
            return
            
        print("\n=== Video Recorder Controls ===")
        print("R - Start/Stop Recording")
        print("C - Capture Frame")
        print("Q - Quit")
        print("================================\n")
        
        try:
            while self.rtscap.isStarted():
                ok, frame = self.rtscap.read_latest_frame()
                
                if not ok:
                    continue
                    
                # 处理帧
                processed_frame = self.process_frame(frame)
                
                # 显示视频
                cv2.imshow("Video Recorder", processed_frame)
                
                # 处理键盘输入
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('r') or key == ord('R'):
                    if self.is_recording:
                        self.stop_recording()
                    else:
                        self.start_recording()
                elif key == ord('c') or key == ord('C'):
                    self.capture_frame(frame)
                    
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        if self.is_recording:
            self.stop_recording()
            
        self.rtscap.stop_read()
        self.rtscap.release()
        cv2.destroyAllWindows()
        
        print(f"\nSession summary:")
        print(f"- Total recorded frames: {self.frame_count}")
        print(f"- Captured frames: {self.captured_frames_count}")
        print(f"- Videos saved to: {self.output_dir}")
        print(f"- Frames saved to: {self.frames_dir}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('python3 video_recorder.py <video_source>')
        print('Examples:')
        print('  python3 video_recorder.py 0  # Use camera 0')
        print('  python3 video_recorder.py "rtsp://example.com/stream"')
        print('  python3 video_recorder.py "http://example.com/stream.m3u8"')
        sys.exit(1)
    
    # 解析输入参数
    source = sys.argv[1]
    if source.isdigit():
        source = int(source)
    
    # 创建并运行录制器
    recorder = VideoRecorder(source)
    recorder.run()


if __name__ == '__main__':
    main()