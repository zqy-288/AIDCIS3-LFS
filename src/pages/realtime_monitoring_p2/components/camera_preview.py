"""
摄像头预览组件
用于实时显示内窥镜摄像头的原始画面，不进行任何图像处理
"""

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal, QTimer, Qt, QMutex, QMutexLocker
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
import time
import logging


class CameraThread(QThread):
    """摄像头采集线程"""
    frameReady = Signal(np.ndarray)
    statusUpdate = Signal(str)
    errorOccurred = Signal(str)
    
    def __init__(self, camera_source=0):
        super().__init__()
        self.camera_source = camera_source
        self.capture = None
        self.is_running = False
        self.mutex = QMutex()
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # 内窥镜设备常用的摄像头源
        self.endoscope_sources = [0, 1, 2, 3]  # 尝试多个摄像头索引
        
    def run(self):
        """线程主循环"""
        try:
            # 尝试打开内窥镜摄像头（支持多个设备索引）
            self.capture = self._open_endoscope_camera()
            if not self.capture or not self.capture.isOpened():
                self.errorOccurred.emit("无法找到内窥镜摄像头设备")
                return
                
            # 设置内窥镜摄像头的专用参数
            self._configure_endoscope_camera()
            
            self.is_running = True
            self.statusUpdate.emit("摄像头已连接")
            
            while self.is_running:
                ret, frame = self.capture.read()
                if ret:
                    # 计算FPS
                    self.frame_count += 1
                    current_time = time.time()
                    if current_time - self.start_time >= 1.0:
                        self.fps = self.frame_count / (current_time - self.start_time)
                        self.frame_count = 0
                        self.start_time = current_time
                    
                    # 发送帧数据
                    self.frameReady.emit(frame)
                else:
                    self.errorOccurred.emit("读取摄像头数据失败")
                    break
                    
                # 控制帧率，避免过度占用资源
                self.msleep(33)  # 约30fps
                
        except Exception as e:
            self.errorOccurred.emit(f"摄像头错误: {str(e)}")
        finally:
            self.stop()
            
    def stop(self):
        """停止摄像头"""
        with QMutexLocker(self.mutex):
            self.is_running = False
            
        if self.capture:
            self.capture.release()
            self.capture = None
            
        self.statusUpdate.emit("摄像头已断开")
        
    def get_fps(self):
        """获取当前帧率"""
        return self.fps
        
    def _open_endoscope_camera(self):
        """尝试打开内窥镜摄像头"""
        # 首先尝试指定的摄像头索引
        cap = cv2.VideoCapture(self.camera_source)
        if cap.isOpened():
            # 测试是否能读取画面
            ret, frame = cap.read()
            if ret and frame is not None:
                self.statusUpdate.emit(f"内窥镜摄像头已连接 (设备索引: {self.camera_source})")
                return cap
            cap.release()
            
        # 如果指定索引失败，尝试其他常见索引
        for source_idx in self.endoscope_sources:
            if source_idx == self.camera_source:
                continue  # 跳过已尝试的索引
                
            self.statusUpdate.emit(f"尝试摄像头设备索引: {source_idx}")
            cap = cv2.VideoCapture(source_idx)
            
            if cap.isOpened():
                # 测试读取
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.camera_source = source_idx  # 更新成功的源索引
                    self.statusUpdate.emit(f"内窥镜摄像头已连接 (设备索引: {source_idx})")
                    return cap
                cap.release()
                
        return None
        
    def _configure_endoscope_camera(self):
        """配置内窥镜摄像头参数"""
        if not self.capture:
            return
            
        # 内窥镜摄像头常用配置
        configs = [
            # 分辨率配置（从高到低尝试）
            (cv2.CAP_PROP_FRAME_WIDTH, 1920),
            (cv2.CAP_PROP_FRAME_HEIGHT, 1080),
            (cv2.CAP_PROP_FRAME_WIDTH, 1280),
            (cv2.CAP_PROP_FRAME_HEIGHT, 720),
            (cv2.CAP_PROP_FRAME_WIDTH, 640),
            (cv2.CAP_PROP_FRAME_HEIGHT, 480),
        ]
        
        # 尝试设置最高分辨率
        width_set = False
        height_set = False
        
        for prop, value in configs:
            if prop == cv2.CAP_PROP_FRAME_WIDTH and not width_set:
                if self.capture.set(prop, value):
                    actual_width = self.capture.get(prop)
                    if actual_width == value:
                        width_set = True
                        self.statusUpdate.emit(f"分辨率宽度设置为: {int(actual_width)}")
                        
            elif prop == cv2.CAP_PROP_FRAME_HEIGHT and not height_set:
                if self.capture.set(prop, value):
                    actual_height = self.capture.get(prop)
                    if actual_height == value:
                        height_set = True
                        self.statusUpdate.emit(f"分辨率高度设置为: {int(actual_height)}")
                        
            if width_set and height_set:
                break
                
        # 其他内窥镜摄像头优化设置
        settings = [
            (cv2.CAP_PROP_FPS, 30),           # 帧率
            (cv2.CAP_PROP_BRIGHTNESS, 0.5),   # 亮度
            (cv2.CAP_PROP_CONTRAST, 0.5),     # 对比度
            (cv2.CAP_PROP_SATURATION, 0.5),   # 饱和度
            (cv2.CAP_PROP_AUTO_EXPOSURE, 0.25), # 自动曝光
        ]
        
        for prop, value in settings:
            try:
                if self.capture.set(prop, value):
                    actual_value = self.capture.get(prop)
                    print(f"设置 {prop}: {actual_value}")
            except Exception as e:
                print(f"无法设置属性 {prop}: {e}")
                
        # 获取最终设置的参数
        final_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        final_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        final_fps = int(self.capture.get(cv2.CAP_PROP_FPS))
        
        self.statusUpdate.emit(f"内窥镜摄像头配置完成: {final_width}x{final_height} @ {final_fps}fps")


class CameraPreviewWidget(QWidget):
    """摄像头预览窗口组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_thread = None
        self.is_previewing = False
        self.current_frame = None
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("等待内窥镜摄像头连接...")
        
        # 信息显示栏
        info_layout = QHBoxLayout()
        self.status_label = QLabel("状态: 未连接")
        self.fps_label = QLabel("FPS: 0")
        self.resolution_label = QLabel("分辨率: -")
        self.device_label = QLabel("设备: 未检测到")
        
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.fps_label)
        info_layout.addWidget(self.resolution_label)
        info_layout.addWidget(self.device_label)
        info_layout.addStretch()
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.preview_button = QPushButton("🔍 开始内窥镜预览")
        self.preview_button.clicked.connect(self.toggle_preview)
        
        self.snapshot_button = QPushButton("📷 保存截图")
        self.snapshot_button.clicked.connect(self.take_snapshot)
        self.snapshot_button.setEnabled(False)
        
        self.detect_button = QPushButton("🔎 检测设备")
        self.detect_button.clicked.connect(self.detect_endoscope_devices)
        
        button_layout.addWidget(self.detect_button)
        button_layout.addWidget(self.preview_button)
        button_layout.addWidget(self.snapshot_button)
        button_layout.addStretch()
        
        # 添加到主布局
        layout.addWidget(self.video_label)
        layout.addLayout(info_layout)
        layout.addLayout(button_layout)
        
        # FPS更新定时器
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_fps)
        self.fps_timer.start(1000)  # 每秒更新一次
        
    def toggle_preview(self):
        """切换预览状态"""
        if not self.is_previewing:
            self.start_preview()
        else:
            self.stop_preview()
            
    def start_preview(self, camera_source=0):
        """开始预览"""
        if self.is_previewing:
            return
            
        self.camera_thread = CameraThread(camera_source)
        self.camera_thread.frameReady.connect(self.update_frame)
        self.camera_thread.statusUpdate.connect(self.update_status)
        self.camera_thread.errorOccurred.connect(self.handle_error)
        
        self.camera_thread.start()
        self.is_previewing = True
        
        self.preview_button.setText("⏹️ 停止内窥镜预览")
        self.snapshot_button.setEnabled(True)
        
    def stop_preview(self):
        """停止预览"""
        if not self.is_previewing:
            return
            
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread.wait()
            self.camera_thread = None
            
        self.is_previewing = False
        self.preview_button.setText("🔍 开始内窥镜预览")
        self.snapshot_button.setEnabled(False)
        
        self.video_label.clear()
        self.video_label.setText("内窥镜预览已停止")
        self.fps_label.setText("FPS: 0")
        self.resolution_label.setText("分辨率: -")
        self.device_label.setText("设备: 已断开")
        
    def update_frame(self, frame):
        """更新显示帧"""
        self.current_frame = frame
        
        # 转换为Qt格式
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        
        # BGR转RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 创建QImage
        q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # 缩放到标签大小
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
        
        # 更新分辨率信息
        self.resolution_label.setText(f"分辨率: {width}x{height}")
        
    def update_fps(self):
        """更新FPS显示"""
        if self.camera_thread and self.is_previewing:
            fps = self.camera_thread.get_fps()
            self.fps_label.setText(f"FPS: {fps:.1f}")
            
    def update_status(self, status):
        """更新状态信息"""
        self.status_label.setText(f"状态: {status}")
        
        # 更新设备信息
        if "设备索引" in status:
            device_idx = status.split("设备索引: ")[1].rstrip(")")
            self.device_label.setText(f"设备: 内窥镜摄像头 (索引{device_idx})")
        elif "已连接" in status:
            self.device_label.setText("设备: 内窥镜摄像头已连接")
        elif "已断开" in status:
            self.device_label.setText("设备: 已断开")
            
        self.logger.info(f"内窥镜摄像头状态: {status}")
        
    def detect_endoscope_devices(self):
        """检测可用的内窥镜设备"""
        self.detect_button.setEnabled(False)
        self.detect_button.setText("🔍 检测中...")
        
        try:
            available_devices = []
            
            # 检测多个可能的摄像头索引
            for i in range(10):  # 检测0-9索引
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # 尝试读取一帧以确认设备有效
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        available_devices.append((i, width, height))
                cap.release()
                
            if available_devices:
                device_info = []
                for idx, width, height in available_devices:
                    device_info.append(f"索引{idx}: {width}x{height}")
                
                from PySide6.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setWindowTitle("检测到的内窥镜设备")
                msg.setText(f"找到 {len(available_devices)} 个可用设备：\n\n" + "\n".join(device_info))
                msg.setIcon(QMessageBox.Information)
                msg.exec()
                
                # 更新设备标签
                self.device_label.setText(f"设备: 找到{len(available_devices)}个可用设备")
            else:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "设备检测", "未检测到可用的内窥镜摄像头设备")
                self.device_label.setText("设备: 未检测到")
                
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "检测错误", f"设备检测失败: {str(e)}")
            
        finally:
            self.detect_button.setEnabled(True)
            self.detect_button.setText("🔎 检测设备")
        
    def handle_error(self, error):
        """处理错误"""
        self.logger.error(f"摄像头错误: {error}")
        QMessageBox.critical(self, "摄像头错误", error)
        self.stop_preview()
        
    def take_snapshot(self):
        """截图保存"""
        if self.current_frame is None:
            return
            
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"
            
            cv2.imwrite(filename, self.current_frame)
            QMessageBox.information(self, "截图成功", f"图片已保存为: {filename}")
            self.logger.info(f"截图保存: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "截图失败", str(e))
            self.logger.error(f"截图失败: {e}")
            
    def get_current_frame(self):
        """获取当前帧"""
        return self.current_frame
        
    def is_active(self):
        """检查预览是否激活"""
        return self.is_previewing


# 测试用例
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建预览窗口
    preview = CameraPreviewWidget()
    preview.setWindowTitle("摄像头预览测试")
    preview.show()
    
    sys.exit(app.exec())