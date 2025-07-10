"""
模拟对象
为报告生成系统测试提供各种模拟对象和辅助类
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock
import threading
import numpy as np


class MockDatabaseManager:
    """模拟数据库管理器"""
    
    def __init__(self, data_file: str = None):
        self.connected = True
        self.data_file = data_file
        self._load_test_data()
        
    def _load_test_data(self):
        """加载测试数据"""
        if self.data_file and os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.workpieces = data.get('workpieces', [])
                self.holes = data.get('holes', [])
                self.measurements = data.get('measurements', [])
                self.defects = data.get('defects', [])
        else:
            self._generate_default_data()
            
    def _generate_default_data(self):
        """生成默认测试数据"""
        # 生成工件数据
        self.workpieces = [
            {
                'id': i + 1,
                'model': f'CP{1400 + (i % 3) * 100}',
                'serial': f'SN-MOCK-{i+1:03d}',
                'operator': ['张工程师', '李技师', '王工程师'][i % 3],
                'created_at': (datetime.now() - timedelta(days=i)).isoformat(),
                'status': 'completed'
            }
            for i in range(5)
        ]
        
        # 生成孔位数据
        self.holes = []
        hole_id = 1
        for workpiece in self.workpieces:
            for j in range(50):  # 每个工件50个孔
                self.holes.append({
                    'id': hole_id,
                    'workpiece_id': workpiece['id'],
                    'hole_number': f'H{j+1:03d}',
                    'position_x': (j % 10) * 15,
                    'position_y': (j // 10) * 15,
                    'target_diameter': 17.6,
                    'measured_diameter': round(17.6 + np.random.normal(0, 0.005), 3),
                    'qualified': j % 20 != 0,  # 5%不合格率
                    'created_at': datetime.now().isoformat()
                })
                hole_id += 1
                
        # 生成测量数据（仅前10个孔位）
        self.measurements = []
        measurement_id = 1
        for hole_id in range(1, 11):
            for k in range(100):  # 每个孔100个测量点
                self.measurements.append({
                    'id': measurement_id,
                    'hole_id': hole_id,
                    'depth': round(k * 0.5, 1),
                    'diameter': round(17.6 + np.random.normal(0, 0.005), 4),
                    'angle': k % 360,
                    'timestamp': datetime.now().timestamp() + k * 0.1
                })
                measurement_id += 1
                
        # 生成缺陷数据
        self.defects = [
            {
                'id': i + 1,
                'hole_id': (i * 5) + 1,  # 每5个孔有一个缺陷
                'defect_type': ['diameter_deviation', 'surface_scratch'][i % 2],
                'severity': ['minor', 'major'][i % 2],
                'description': f'模拟缺陷 {i + 1}',
                'detected_at': datetime.now().isoformat()
            }
            for i in range(10)
        ]
        
    def get_all_hole_data(self) -> List[Dict]:
        """获取所有孔位数据"""
        return [
            {
                'hole_id': hole['hole_number'],
                'min_diameter': hole['measured_diameter'] - 0.002,
                'max_diameter': hole['measured_diameter'] + 0.002,
                'avg_diameter': hole['measured_diameter'],
                'qualified': hole['qualified'],
                'surface_defects': 'None' if hole['qualified'] else 'Diameter deviation',
                'position_x': hole['position_x'],
                'position_y': hole['position_y']
            }
            for hole in self.holes
        ]
        
    def get_measurement_data_for_hole(self, hole_id: str) -> List[Dict]:
        """获取特定孔位的测量数据"""
        # 简化：返回模拟数据
        return [
            {
                'depth': i * 0.5,
                'diameter': 17.6 + np.random.normal(0, 0.005)
            }
            for i in range(500)
        ]
        
    def get_endoscope_images_for_hole(self, hole_id: str) -> List[str]:
        """获取内窥镜图像路径"""
        # 返回空列表，触发占位符图像生成
        return []
        
    def get_workpiece_by_id(self, workpiece_id: int) -> Optional[Dict]:
        """根据ID获取工件信息"""
        for workpiece in self.workpieces:
            if workpiece['id'] == workpiece_id:
                return workpiece
        return None
        
    def get_holes_by_workpiece(self, workpiece_id: int) -> List[Dict]:
        """获取指定工件的所有孔位"""
        return [hole for hole in self.holes if hole['workpiece_id'] == workpiece_id]
        
    def get_defects_by_hole(self, hole_id: int) -> List[Dict]:
        """获取指定孔位的缺陷"""
        return [defect for defect in self.defects if defect['hole_id'] == hole_id]


class MockReportGenerator:
    """模拟报告生成器"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or MockDatabaseManager()
        self.output_dir = Path("mock_output")
        self.temp_dir = Path("mock_temp")
        self.company_name = "模拟数字化检测系统"
        
        # 确保目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
    def export_raw_data_csv(self, hole_data: Dict, workpiece_info: Dict) -> str:
        """模拟CSV导出"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mock_data_{workpiece_info.get('model', 'TEST')}_{timestamp}.csv"
        file_path = self.output_dir / filename
        
        # 创建模拟CSV内容
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write("孔位ID,最小直径(mm),最大直径(mm),平均直径(mm),检测状态\n")
            for i in range(hole_data.get('total_holes', 10)):
                f.write(f"H{i+1:03d},17.595,17.605,17.600,合格\n")
                
        return str(file_path)
        
    def generate_web_report_data(self, hole_data: Dict, workpiece_info: Dict) -> Dict:
        """模拟Web报告数据生成"""
        return {
            'header': {
                'report_id': f"MOCK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'workpiece_model': workpiece_info.get('model', 'TEST'),
                'workpiece_serial': workpiece_info.get('serial', 'SN-MOCK'),
                'operator': workpiece_info.get('operator', '模拟用户'),
                'generated_at': datetime.now().isoformat()
            },
            'summary': {
                'total_holes': hole_data.get('total_holes', 10),
                'checked_holes': hole_data.get('checked_holes', 10),
                'qualified_holes': hole_data.get('qualified_holes', 9),
                'unqualified_holes': hole_data.get('unqualified_holes', 1),
                'qualification_rate': 90.0
            },
            'non_conformities': [],
            'charts': {},
            'images': {},
            'full_data': []
        }


class MockEnhancedReportGenerator(MockReportGenerator):
    """模拟增强报告生成器"""
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.chart_temp_dir = Path("mock_charts")
        self.chart_temp_dir.mkdir(exist_ok=True)
        
    def generate_envelope_chart_with_annotations(self, measurement_data: List[Dict],
                                               target_diameter: float,
                                               upper_tolerance: float,
                                               lower_tolerance: float,
                                               hole_id: str = "") -> str:
        """模拟包络图生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mock_envelope_{hole_id}_{timestamp}.png"
        file_path = self.chart_temp_dir / filename
        
        # 创建模拟图像文件
        with open(file_path, 'wb') as f:
            # 写入最小的PNG文件头（模拟）
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            
        return str(file_path)
        
    def generate_endoscope_panorama(self, endoscope_images: List[str],
                                  hole_id: str = "") -> str:
        """模拟内窥镜全景图生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mock_panorama_{hole_id}_{timestamp}.png"
        file_path = self.chart_temp_dir / filename
        
        # 创建模拟图像文件
        with open(file_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 150)
            
        return str(file_path)
        
    def _generate_placeholder_endoscope_image(self, hole_id: str = "") -> str:
        """模拟占位符内窥镜图像"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mock_placeholder_{hole_id}_{timestamp}.png"
        file_path = self.chart_temp_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 80)
            
        return str(file_path)


class MockReportGenerationThread:
    """模拟报告生成线程"""
    
    def __init__(self, generator, report_type: str, hole_data: Dict, workpiece_info: Dict):
        self.generator = generator
        self.report_type = report_type
        self.hole_data = hole_data
        self.workpiece_info = workpiece_info
        
        # 模拟信号
        self.progress_updated = MockSignal()
        self.status_updated = MockSignal()
        self.generation_completed = MockSignal()
        self.generation_failed = MockSignal()
        
        self._is_running = False
        
    def start(self):
        """启动线程"""
        self._is_running = True
        threading.Thread(target=self.run, daemon=True).start()
        
    def run(self):
        """运行报告生成"""
        try:
            self.status_updated.emit("开始生成...")
            self.progress_updated.emit(10)
            time.sleep(0.1)
            
            if self.report_type == "CSV":
                file_path = self.generator.export_raw_data_csv(
                    self.hole_data, self.workpiece_info
                )
            elif self.report_type == "WEB":
                web_data = self.generator.generate_web_report_data(
                    self.hole_data, self.workpiece_info
                )
                # 保存Web数据
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mock_web_{timestamp}.json"
                file_path = self.generator.output_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(web_data, f, ensure_ascii=False, indent=2)
                file_path = str(file_path)
            else:
                raise ValueError(f"不支持的报告类型: {self.report_type}")
                
            self.progress_updated.emit(50)
            time.sleep(0.1)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("生成完成")
            self.generation_completed.emit(self.report_type, file_path)
            
        except Exception as e:
            self.generation_failed.emit(self.report_type, str(e))
        finally:
            self._is_running = False
            
    def wait(self, timeout: int = 5000):
        """等待线程完成"""
        start_time = time.time()
        while self._is_running and (time.time() - start_time) * 1000 < timeout:
            time.sleep(0.01)
        return not self._is_running


class MockSignal:
    """模拟Qt信号"""
    
    def __init__(self):
        self._handlers = []
        
    def connect(self, handler):
        """连接信号处理器"""
        self._handlers.append(handler)
        
    def emit(self, *args, **kwargs):
        """发射信号"""
        for handler in self._handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                print(f"Signal handler error: {e}")


class MockQWidget:
    """模拟QWidget"""
    
    def __init__(self):
        self.children = []
        self.layout = None
        
    def setLayout(self, layout):
        self.layout = layout


class MockQProgressBar:
    """模拟进度条"""
    
    def __init__(self):
        self.value = 0
        self.minimum = 0
        self.maximum = 100
        
    def setValue(self, value):
        self.value = max(self.minimum, min(self.maximum, value))
        
    def setRange(self, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum


class MockQLabel:
    """模拟标签"""
    
    def __init__(self, text=""):
        self.text = text
        
    def setText(self, text):
        self.text = str(text)


class MockQLineEdit:
    """模拟文本输入框"""
    
    def __init__(self, text=""):
        self._text = text
        
    def text(self):
        return self._text
        
    def setText(self, text):
        self._text = str(text)


class MockQPushButton:
    """模拟按钮"""
    
    def __init__(self, text=""):
        self.text = text
        self._enabled = True
        self.clicked = MockSignal()
        
    def setEnabled(self, enabled):
        self._enabled = bool(enabled)
        
    def isEnabled(self):
        return self._enabled
        
    def setText(self, text):
        self.text = str(text)


class MockReportManagerWidget:
    """模拟报告管理器组件"""
    
    def __init__(self):
        # UI组件
        self.model_input = MockQLineEdit()
        self.serial_input = MockQLineEdit()
        self.operator_input = MockQLineEdit()
        self.progress_bar = MockQProgressBar()
        self.status_label = MockQLabel("准备就绪")
        
        # 按钮
        self.pdf_button = MockQPushButton("生成PDF报告")
        self.web_button = MockQPushButton("生成Web报告")
        self.excel_button = MockQPushButton("导出Excel")
        self.csv_button = MockQPushButton("导出CSV")
        
        # 报告生成器
        self.report_generator = MockReportGenerator()
        self.enhanced_generator = MockEnhancedReportGenerator()
        
        # 输出目录
        self.output_dir = Path("mock_reports")
        self.output_dir.mkdir(exist_ok=True)
        
    def get_workpiece_info(self) -> Dict:
        """获取工件信息"""
        return {
            'model': self.model_input.text(),
            'serial': self.serial_input.text(),
            'operator': self.operator_input.text(),
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
    def validate_inputs(self) -> tuple[bool, str]:
        """验证输入"""
        if not self.model_input.text():
            return False, "请输入产品型号"
        if not self.serial_input.text():
            return False, "请输入工件序列号"
        if not self.operator_input.text():
            return False, "请输入操作员姓名"
        return True, ""
        
    def update_progress(self, value: int):
        """更新进度"""
        self.progress_bar.setValue(value)
        
    def update_status(self, status: str):
        """更新状态"""
        self.status_label.setText(status)
        
    def generate_csv_report(self) -> str:
        """生成CSV报告"""
        workpiece_info = self.get_workpiece_info()
        hole_data = {'total_holes': 100, 'checked_holes': 100}
        
        self.update_status("正在生成CSV报告...")
        self.update_progress(50)
        
        file_path = self.report_generator.export_raw_data_csv(hole_data, workpiece_info)
        
        self.update_progress(100)
        self.update_status("CSV报告生成完成")
        
        return file_path


class MockTestDataProvider:
    """模拟测试数据提供者"""
    
    @staticmethod
    def get_sample_workpiece_info() -> Dict:
        """获取样本工件信息"""
        return {
            'model': 'CP1400',
            'serial': 'SN-SAMPLE-001',
            'operator': '样本用户',
            'start_time': datetime.now() - timedelta(hours=1),
            'end_time': datetime.now(),
            'equipment_id': 'AIDCIS-MOCK-001',
            'batch_number': 'BATCH-MOCK-001'
        }
        
    @staticmethod
    def get_sample_hole_data() -> Dict:
        """获取样本孔位数据"""
        return {
            'total_holes': 100,
            'current_hole_id': 'H050',
            'checked_holes': 98,
            'qualified_holes': 95,
            'unqualified_holes': 3
        }
        
    @staticmethod
    def get_sample_measurement_data() -> List[Dict]:
        """获取样本测量数据"""
        return [
            {
                'depth': i * 0.5,
                'diameter': 17.6 + np.random.normal(0, 0.005)
            }
            for i in range(1000)
        ]
        
    @staticmethod
    def get_sample_defect_annotations() -> List[Dict]:
        """获取样本缺陷标注"""
        return [
            {
                'bbox': [100, 100, 200, 200],
                'label': '表面划痕',
                'confidence': 0.95,
                'severity': 'minor'
            },
            {
                'bbox': [300, 150, 400, 250],
                'label': '孔径偏差',
                'confidence': 0.88,
                'severity': 'major'
            }
        ]


def create_mock_environment():
    """创建完整的模拟测试环境"""
    # 创建模拟对象
    db_manager = MockDatabaseManager()
    report_generator = MockReportGenerator(db_manager)
    enhanced_generator = MockEnhancedReportGenerator(db_manager)
    widget = MockReportManagerWidget()
    data_provider = MockTestDataProvider()
    
    # 返回环境字典
    return {
        'db_manager': db_manager,
        'report_generator': report_generator,
        'enhanced_generator': enhanced_generator,
        'widget': widget,
        'data_provider': data_provider
    }


def cleanup_mock_files():
    """清理模拟文件"""
    mock_dirs = [
        Path("mock_output"),
        Path("mock_temp"),
        Path("mock_charts"),
        Path("mock_reports")
    ]
    
    for mock_dir in mock_dirs:
        if mock_dir.exists():
            import shutil
            shutil.rmtree(mock_dir, ignore_errors=True)


if __name__ == '__main__':
    print("=" * 60)
    print("模拟对象测试")
    print("=" * 60)
    
    # 创建模拟环境
    env = create_mock_environment()
    
    # 测试模拟数据库
    print("🔧 测试模拟数据库...")
    hole_data = env['db_manager'].get_all_hole_data()
    print(f"   获取孔位数据: {len(hole_data)} 个孔位")
    
    # 测试模拟报告生成器
    print("📊 测试模拟报告生成器...")
    workpiece_info = env['data_provider'].get_sample_workpiece_info()
    hole_data_dict = env['data_provider'].get_sample_hole_data()
    
    csv_path = env['report_generator'].export_raw_data_csv(hole_data_dict, workpiece_info)
    print(f"   CSV报告: {csv_path}")
    
    web_data = env['report_generator'].generate_web_report_data(hole_data_dict, workpiece_info)
    print(f"   Web数据: {len(web_data)} 个字段")
    
    # 测试增强生成器
    print("🎨 测试增强报告生成器...")
    measurement_data = env['data_provider'].get_sample_measurement_data()
    
    envelope_chart = env['enhanced_generator'].generate_envelope_chart_with_annotations(
        measurement_data, 17.6, 0.05, 0.07, "H050"
    )
    print(f"   包络图: {envelope_chart}")
    
    placeholder = env['enhanced_generator']._generate_placeholder_endoscope_image("H050")
    print(f"   占位符图像: {placeholder}")
    
    # 测试组件
    print("🖥️ 测试UI组件...")
    env['widget'].model_input.setText("CP1400")
    env['widget'].serial_input.setText("SN-UI-TEST")
    env['widget'].operator_input.setText("测试用户")
    
    is_valid, error = env['widget'].validate_inputs()
    print(f"   输入验证: {'通过' if is_valid else f'失败 - {error}'}")
    
    env['widget'].update_progress(75)
    env['widget'].update_status("测试完成")
    print(f"   进度: {env['widget'].progress_bar.value}%")
    print(f"   状态: {env['widget'].status_label.text}")
    
    print("\n✅ 所有模拟对象测试完成")
    
    # 清理
    cleanup_mock_files()
    print("🧹 清理完成")