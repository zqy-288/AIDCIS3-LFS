"""
Base test case for Qt application testing.
Provides common setup and teardown for all test cases.
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Try PySide6 first, then fallback to PyQt5
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from PySide6.QtTest import QTest
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        from PyQt5.QtTest import QTest
    except ImportError:
        # Create mock classes if Qt is not available
        class QApplication:
            def __init__(self, *args): pass
            @staticmethod
            def instance(): return None
            def quit(self): pass
        
        class QTimer:
            def __init__(self): pass
            def start(self): pass
            def stop(self): pass
        
        class QTest:
            @staticmethod
            def qWait(ms): 
                import time
                time.sleep(ms / 1000.0)


class BaseTestCase(unittest.TestCase):
    """
    Base test case that handles Qt application initialization and common fixtures.
    All test classes should inherit from this class.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up Qt application for the entire test class."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
        
        # Prevent the application from exiting when tests complete
        cls.app.setQuitOnLastWindowClosed(False)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up Qt application after all tests in the class."""
        # Process any remaining events
        cls.app.processEvents()
        
        # Don't quit the application here as it might be shared between test classes
        pass
    
    def setUp(self):
        """Set up each individual test."""
        super().setUp()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock common dependencies
        self.mock_database = self.create_mock_database()
        self.mock_config = self.create_mock_config()
        self.mock_logger = self.create_mock_logger()
        
        # Setup patches that are commonly used
        self.database_patcher = patch('src.data.repositories.DatabaseConnection')
        self.config_patcher = patch('src.core.default_configuration_manager.ConfigManager')
        self.logger_patcher = patch('src.core.logger.get_logger')
        
        self.mock_db_connection = self.database_patcher.start()
        self.mock_config_manager = self.config_patcher.start()
        self.mock_logger_instance = self.logger_patcher.start()
        
        self.mock_db_connection.return_value = self.mock_database
        self.mock_config_manager.return_value = self.mock_config
        self.mock_logger_instance.return_value = self.mock_logger
    
    def tearDown(self):
        """Clean up each individual test."""
        super().tearDown()
        
        # Stop all patches
        self.database_patcher.stop()
        self.config_patcher.stop()
        self.logger_patcher.stop()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Process any remaining Qt events
        QApplication.processEvents()
    
    def create_mock_database(self):
        """Create a mock database connection with common methods."""
        mock_db = Mock()
        mock_db.execute.return_value = Mock()
        mock_db.fetchall.return_value = []
        mock_db.fetchone.return_value = None
        mock_db.commit.return_value = None
        mock_db.rollback.return_value = None
        mock_db.close.return_value = None
        return mock_db
    
    def create_mock_config(self):
        """Create a mock configuration object with default values."""
        mock_config = Mock()
        mock_config.get.return_value = "default_value"
        mock_config.set.return_value = None
        mock_config.save.return_value = None
        mock_config.load.return_value = None
        return mock_config
    
    def create_mock_logger(self):
        """Create a mock logger object."""
        mock_logger = Mock()
        mock_logger.info.return_value = None
        mock_logger.debug.return_value = None
        mock_logger.warning.return_value = None
        mock_logger.error.return_value = None
        mock_logger.critical.return_value = None
        return mock_logger
    
    def create_test_data_file(self, filename, content="test data"):
        """Create a temporary test data file."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def wait_for_signal(self, signal, timeout=1000):
        """Wait for a Qt signal to be emitted within timeout milliseconds."""
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        signal.connect(loop.quit)
        timer.start(timeout)
        loop.exec_()
        timer.stop()
    
    def assert_signal_emitted(self, signal, callable_func, *args, **kwargs):
        """Assert that a signal is emitted when calling a function."""
        signal_spy = []
        signal.connect(lambda *args: signal_spy.append(args))
        
        callable_func(*args, **kwargs)
        QApplication.processEvents()
        
        self.assertTrue(len(signal_spy) > 0, f"Signal {signal} was not emitted")
        return signal_spy
    
    def simulate_user_interaction(self, widget, delay_ms=100):
        """Simulate user interaction with a delay to allow Qt event processing."""
        QTest.qWait(delay_ms)
        QApplication.processEvents()


class QtTestCase(BaseTestCase):
    """
    Specialized test case for Qt widget testing.
    Provides additional utilities for widget testing.
    """
    
    def setUp(self):
        """Set up Qt widget testing environment."""
        super().setUp()
        self.widgets_to_close = []
    
    def tearDown(self):
        """Clean up Qt widgets."""
        # Close all widgets that were created during tests
        for widget in self.widgets_to_close:
            if widget and hasattr(widget, 'close'):
                widget.close()
        
        super().tearDown()
    
    def create_widget(self, widget_class, *args, **kwargs):
        """Create a widget and register it for cleanup."""
        widget = widget_class(*args, **kwargs)
        self.widgets_to_close.append(widget)
        return widget
    
    def show_widget(self, widget):
        """Show a widget and wait for it to be displayed."""
        widget.show()
        QTest.qWaitForWindowExposed(widget)
        return widget


# QEventLoop import is handled in the compatibility section above
try:
    from PySide6.QtCore import QEventLoop
except ImportError:
    try:
        from PyQt5.QtCore import QEventLoop
    except ImportError:
        class QEventLoop:
            def __init__(self): pass
            def exec_(self): pass
            def quit(self): pass


class AsyncTestCase(BaseTestCase):
    """
    Test case for testing asynchronous operations and signals.
    """
    
    def run_async_test(self, async_func, timeout=5000):
        """Run an async function and wait for completion."""
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        
        # Mock async completion
        def on_complete():
            loop.quit()
        
        timer.start(timeout)
        async_func(on_complete)
        loop.exec_()
        timer.stop()