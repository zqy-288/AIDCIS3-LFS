"""
Pytest configuration and shared fixtures.
Provides global test configuration and commonly used fixtures.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import Qt application for testing
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    import PySide6.QtTest as QTest
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        import PyQt5.QtTest as QTest
    except ImportError:
        QApplication = None
        QTimer = None
        QTest = None

from tests.fixtures.test_data_fixtures import TestDataFixtures, MockDataFixtures, FileFixtures


# Global Qt Application for testing
_qapp = None


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set up Qt application for testing
    global _qapp
    if QApplication and not QApplication.instance():
        _qapp = QApplication([])
        _qapp.setQuitOnLastWindowClosed(False)


def pytest_unconfigure(config):
    """Clean up after pytest."""
    global _qapp
    if _qapp:
        _qapp.quit()
        _qapp = None


@pytest.fixture(scope="session")
def qapp():
    """Qt application fixture for the entire test session."""
    global _qapp
    if not _qapp and QApplication:
        _qapp = QApplication([])
        _qapp.setQuitOnLastWindowClosed(False)
    return _qapp


@pytest.fixture(scope="function")
def temp_dir():
    """Temporary directory fixture."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def mock_database():
    """Mock database fixture."""
    return MockDataFixtures.create_mock_database()


@pytest.fixture(scope="function")
def mock_dxf_parser():
    """Mock DXF parser fixture."""
    return MockDataFixtures.create_mock_dxf_parser()


@pytest.fixture(scope="function")
def mock_graphics_scene():
    """Mock graphics scene fixture."""
    return MockDataFixtures.create_mock_graphics_scene()


@pytest.fixture(scope="function")
def mock_status_manager():
    """Mock status manager fixture."""
    return MockDataFixtures.create_mock_status_manager()


@pytest.fixture(scope="function")
def mock_panorama_controller():
    """Mock panorama controller fixture."""
    return MockDataFixtures.create_mock_panorama_controller()


@pytest.fixture(scope="function")
def sample_holes():
    """Sample holes fixture."""
    return TestDataFixtures.create_sample_holes(10)


@pytest.fixture(scope="function")
def hole_collection():
    """Hole collection fixture."""
    return TestDataFixtures.create_hole_collection(20)


@pytest.fixture(scope="function")
def main_view_model():
    """Main view model fixture."""
    return TestDataFixtures.create_main_view_model()


@pytest.fixture(scope="function")
def test_dxf_file(temp_dir):
    """Test DXF file fixture."""
    file_path = FileFixtures.create_test_dxf_file()
    yield file_path
    # Cleanup
    try:
        os.unlink(file_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def test_database_file(temp_dir):
    """Test database file fixture."""
    file_path = FileFixtures.create_test_database_file()
    yield file_path
    # Cleanup
    try:
        os.unlink(file_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def test_config_file(temp_dir):
    """Test configuration file fixture."""
    file_path = FileFixtures.create_test_config_file()
    yield file_path
    # Cleanup
    try:
        os.unlink(file_path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for each test."""
    # Store original sys.path
    original_path = sys.path.copy()
    
    # Add project root to path if not already there
    project_root = os.path.join(os.path.dirname(__file__), '..')
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    yield
    
    # Restore original sys.path
    sys.path[:] = original_path


@pytest.fixture(scope="function")
def isolated_modules():
    """Fixture that provides module isolation for testing."""
    # Store original modules
    original_modules = sys.modules.copy()
    
    yield
    
    # Remove any modules that were imported during the test
    # This helps prevent test pollution
    modules_to_remove = []
    for module_name in sys.modules:
        if module_name not in original_modules:
            if module_name.startswith('src.') or module_name.startswith('tests.'):
                modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        if module_name in sys.modules:
            del sys.modules[module_name]


@pytest.fixture(scope="function")
def patch_imports():
    """Fixture that provides import patching utilities."""
    patches = []
    
    def add_patch(target, **kwargs):
        patcher = patch(target, **kwargs)
        mock = patcher.start()
        patches.append(patcher)
        return mock
    
    yield add_patch
    
    # Clean up all patches
    for patcher in patches:
        patcher.stop()


# Pytest markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow
pytest.mark.qt = pytest.mark.qt


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Add qt marker for tests that use Qt
        if "qt" in item.name.lower() or "widget" in item.name.lower():
            item.add_marker(pytest.mark.qt)
        
        # Add slow marker for tests that might take longer
        if "integration" in str(item.fspath) or "performance" in str(item.fspath):
            item.add_marker(pytest.mark.slow)


# Custom assertions for testing
def assert_signal_emitted(signal, timeout=1000):
    """Assert that a Qt signal is emitted within timeout."""
    if not QTest:
        pytest.skip("Qt testing not available")
    
    received = []
    
    def slot(*args):
        received.append(args)
    
    signal.connect(slot)
    
    # Wait for signal
    QTest.qWait(timeout)
    
    assert len(received) > 0, f"Signal {signal} was not emitted within {timeout}ms"
    return received


def assert_view_model_valid(view_model):
    """Assert that a view model is in a valid state."""
    if hasattr(view_model, 'validate'):
        errors = view_model.validate()
        assert len(errors) == 0, f"View model validation failed: {errors}"
    
    # Check basic properties
    assert hasattr(view_model, 'detection_progress')
    assert 0 <= view_model.detection_progress <= 100
    
    if hasattr(view_model, 'status_summary'):
        assert isinstance(view_model.status_summary, dict)
        for count in view_model.status_summary.values():
            assert count >= 0


# Add custom assertions to pytest namespace
pytest.assert_signal_emitted = assert_signal_emitted
pytest.assert_view_model_valid = assert_view_model_valid


# Playwright fixtures
@pytest.fixture(scope="session")
def playwright():
    """提供 Playwright 实例"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            yield p
    except ImportError:
        pytest.skip("Playwright not installed")


@pytest.fixture(scope="session")
def browser(playwright):
    """提供浏览器实例"""
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """提供页面实例"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()