"""
pytest配置文件
提供测试fixtures和共享配置
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 模拟PySide6，避免在测试环境中依赖GUI
pyside6_mock = MagicMock()
pyside6_mock.__version__ = "6.7.0"
sys.modules['PySide6'] = pyside6_mock

# 创建QtCore mock并添加必要的属性
qtcore_mock = MagicMock()
qtcore_mock.__version__ = "6.7.0"
qtcore_mock.qVersion = MagicMock(return_value="6.7.0")
sys.modules['PySide6.QtCore'] = qtcore_mock

sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()

# 模拟Qt信号和槽
class MockSignal:
    def __init__(self, *args):
        self.connections = []
        self.args = args
    
    def connect(self, slot):
        self.connections.append(slot)
    
    def emit(self, *args, **kwargs):
        for connection in self.connections:
            connection(*args, **kwargs)
    
    def disconnect(self, slot=None):
        if slot is None:
            self.connections.clear()
        elif slot in self.connections:
            self.connections.remove(slot)

class MockQObject:
    def __init__(self):
        pass

# 设置Mock对象
sys.modules['PySide6.QtCore'].QObject = MockQObject
sys.modules['PySide6.QtCore'].pyqtSignal = MockSignal
sys.modules['PySide6.QtCore'].Signal = MockSignal
sys.modules['PySide6.QtCore'].QTimer = MagicMock()

# 确保QtCore有必要的版本属性
sys.modules['PySide6.QtCore'].__version__ = "6.7.0"

@pytest.fixture(scope="session")
def project_root_path():
    """提供项目根目录路径"""
    return project_root

@pytest.fixture(scope="function")
def mock_qt_app():
    """模拟Qt应用程序"""
    with patch('PySide6.QtWidgets.QApplication') as mock_app:
        mock_app.instance.return_value = None
        yield mock_app

@pytest.fixture(scope="function")
def mock_event_bus():
    """模拟事件总线"""
    class MockEventBus:
        def __init__(self):
            self.subscribers = {}
            self.published_events = []
        
        def subscribe(self, event_type: str, callback: callable):
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
        
        def unsubscribe(self, event_type: str, callback: callable):
            if event_type in self.subscribers:
                self.subscribers[event_type].remove(callback)
        
        def publish(self, event_type: str, data: Dict[str, Any] = None):
            self.published_events.append({'type': event_type, 'data': data})
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    callback(data)
        
        def clear(self):
            self.subscribers.clear()
            self.published_events.clear()
    
    return MockEventBus()

@pytest.fixture(scope="function")
def mock_dependency_container():
    """模拟依赖注入容器"""
    class MockDependencyContainer:
        def __init__(self):
            self.instances = {}
            self.factories = {}
        
        def register_instance(self, interface, instance):
            self.instances[interface] = instance
        
        def register_factory(self, interface, factory):
            self.factories[interface] = factory
        
        def resolve(self, interface):
            if interface in self.instances:
                return self.instances[interface]
            elif interface in self.factories:
                return self.factories[interface]()
            return None
        
        def clear(self):
            self.instances.clear()
            self.factories.clear()
    
    return MockDependencyContainer()

@pytest.fixture(scope="function")
def mock_hole_collection():
    """模拟孔位集合"""
    from unittest.mock import Mock
    from enum import Enum
    
    try:
        from src.core_business.models.hole_data import HoleData, HoleStatus
    except ImportError:
        # 如果导入失败，创建模拟的HoleData和HoleStatus
        class HoleStatus(Enum):
            PENDING = "pending"
            DETECTING = "detecting"
            QUALIFIED = "qualified"
            DEFECTIVE = "defective"
        
        class HoleData:
            def __init__(self, hole_id, center_x, center_y, radius, status):
                self.hole_id = hole_id
                self.center_x = center_x
                self.center_y = center_y
                self.radius = radius
                self.status = status
    
    holes = {}
    for i in range(5):
        hole_id = f"H{i:03d}"
        hole = HoleData(
            hole_id=hole_id,
            center_x=float(i * 10),
            center_y=float(i * 10),
            radius=5.0,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    mock_collection = Mock()
    mock_collection.holes = holes
    mock_collection.total_count = len(holes)
    mock_collection.get_hole.side_effect = lambda hole_id: holes.get(hole_id)
    mock_collection.__len__ = Mock(return_value=len(holes))
    mock_collection.__iter__ = Mock(return_value=iter(holes.values()))
    mock_collection.__bool__ = Mock(return_value=True)  # 确保集合被认为是非空的
    
    # 添加专门的方法用于统计计算
    def get_count_by_status(status):
        return sum(1 for hole in holes.values() if hole.status == status)
    
    mock_collection.get_count_by_status = get_count_by_status
    
    return mock_collection

@pytest.fixture(scope="function")
def mock_detection_state_manager():
    """模拟检测状态管理器"""
    from src.models.detection_state import DetectionState
    
    class MockDetectionStateManager:
        def __init__(self):
            self.current_state = DetectionState.IDLE
            self.state_history = []
            self.callbacks = []
        
        def add_state_change_callback(self, callback):
            self.callbacks.append(callback)
        
        def remove_state_change_callback(self, callback):
            if callback in self.callbacks:
                self.callbacks.remove(callback)
        
        def transition_to(self, new_state, reason=""):
            old_state = self.current_state
            if self.current_state.can_transition_to(new_state):
                self.current_state = new_state
                self.state_history.append({
                    'old_state': old_state,
                    'new_state': new_state,
                    'reason': reason
                })
                for callback in self.callbacks:
                    callback(old_state, new_state)
                return True
            return False
        
        def can_transition_to(self, target_state):
            return self.current_state.can_transition_to(target_state)
        
        def reset_to_idle(self, reason=""):
            return self.transition_to(DetectionState.IDLE, reason)
    
    return MockDetectionStateManager()

@pytest.fixture(scope="function")
def sample_workpiece_data():
    """提供示例工件数据"""
    return {
        'workpiece_id': 'WP-TEST-001',
        'name': 'Test Workpiece',
        'total_holes': 100,
        'dimensions': {
            'width': 1000.0,
            'height': 800.0,
            'thickness': 50.0
        },
        'material': 'Steel',
        'created_date': '2025-01-18T10:00:00',
        'metadata': {
            'project': 'Test Project',
            'operator': 'Test User'
        }
    }

@pytest.fixture(scope="function")
def sample_detection_results():
    """提供示例检测结果"""
    return {
        'H001': {
            'hole_id': 'H001',
            'status': 'qualified',
            'diameter': 10.2,
            'position_x': 100.5,
            'position_y': 200.3,
            'confidence': 0.95,
            'timestamp': '2025-01-18T10:05:00'
        },
        'H002': {
            'hole_id': 'H002',
            'status': 'defective',
            'diameter': 9.8,
            'position_x': 150.2,
            'position_y': 250.1,
            'confidence': 0.88,
            'defect_type': 'size_deviation',
            'timestamp': '2025-01-18T10:06:00'
        }
    }

@pytest.fixture(scope="function", autouse=True)
def reset_mocks():
    """在每个测试后重置Mock对象"""
    yield
    # 清理可能的模块级别状态

@pytest.fixture(scope="function")
def mock_logger():
    """模拟日志记录器"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger

@pytest.fixture(scope="function")
def mock_file_system(tmp_path):
    """模拟文件系统"""
    # 创建临时目录结构
    test_data_dir = tmp_path / "test_data"
    test_data_dir.mkdir()
    
    # 创建示例DXF文件
    dxf_file = test_data_dir / "test.dxf"
    dxf_file.write_text("TEST DXF CONTENT")
    
    # 创建配置目录
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    return {
        'root': tmp_path,
        'test_data': test_data_dir,
        'config': config_dir,
        'dxf_file': dxf_file
    }

@pytest.fixture(scope="function")
def mock_qt_widgets():
    """模拟Qt控件"""
    widgets = {
        'QMainWindow': Mock(),
        'QWidget': Mock(),
        'QTabWidget': Mock(),
        'QVBoxLayout': Mock(),
        'QHBoxLayout': Mock(),
        'QLabel': Mock(),
        'QPushButton': Mock(),
        'QProgressBar': Mock(),
        'QMenuBar': Mock(),
        'QStatusBar': Mock()
    }
    
    for name, widget in widgets.items():
        setattr(sys.modules['PySide6.QtWidgets'], name, widget)
    
    return widgets

class MockTabInfo:
    """模拟选项卡信息"""
    def __init__(self, tab_id, title, tab_type, controller=None):
        self.tab_id = tab_id
        self.title = title
        self.tab_type = tab_type
        self.controller = controller

@pytest.fixture(scope="function")
def mock_tab_manager():
    """模拟选项卡管理器"""
    class MockTabManager:
        def __init__(self):
            self.tabs = {}
            self.current_tab_id = None
            self.tab_switched_callbacks = []
        
        def create_tabs(self, parent):
            mock_widget = Mock()
            return mock_widget
        
        def add_tab(self, tab_id, title, widget, tab_type):
            tab_info = MockTabInfo(tab_id, title, tab_type)
            self.tabs[tab_id] = tab_info
            return tab_info
        
        def remove_tab(self, tab_id):
            if tab_id in self.tabs:
                del self.tabs[tab_id]
        
        def switch_tab(self, tab_id):
            if tab_id in self.tabs:
                old_tab_id = self.current_tab_id
                self.current_tab_id = tab_id
                for callback in self.tab_switched_callbacks:
                    callback(old_tab_id, tab_id)
                return True
            return False
        
        def get_tab_info(self, tab_id):
            return self.tabs.get(tab_id)
        
        def get_all_tab_ids(self):
            return list(self.tabs.keys())
        
        def cleanup(self):
            self.tabs.clear()
    
    return MockTabManager()

# 测试运行前的全局设置
def pytest_configure(config):
    """pytest配置"""
    # 设置测试标记
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """修改测试项目集合"""
    # 为没有标记的测试添加默认标记
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)