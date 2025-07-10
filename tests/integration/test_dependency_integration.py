"""
IT-010: 依赖冲突处理集成测试
验证AIDCIS2组件与主应用程序依赖项的兼容性
"""

import pytest
import sys
import importlib
import warnings
from packaging import version


class TestDependencyIntegration:
    """依赖冲突处理集成测试类"""
    
    def test_critical_dependencies_import(self):
        """测试关键依赖项导入"""
        critical_deps = [
            'PySide6',
            'numpy',
            'ezdxf',
            'pyqtgraph',
            'sqlalchemy',  # 修正导入名称
            'matplotlib'
        ]
        
        failed_imports = []
        for dep in critical_deps:
            try:
                importlib.import_module(dep)
                print(f"✅ {dep} 导入成功")
            except ImportError as e:
                failed_imports.append((dep, str(e)))
                print(f"❌ {dep} 导入失败: {e}")
        
        assert len(failed_imports) == 0, f"依赖导入失败: {failed_imports}"
    
    def test_pyside6_version_compatibility(self):
        """测试PySide6版本兼容性"""
        import PySide6
        
        current_version = version.parse(PySide6.__version__)
        min_required = version.parse("6.5.0")
        target_version = version.parse("6.9.1")
        
        print(f"当前PySide6版本: {current_version}")
        print(f"最低要求版本: {min_required}")
        print(f"目标版本: {target_version}")
        
        # 验证版本满足最低要求
        assert current_version >= min_required, f"PySide6版本过低: {current_version} < {min_required}"
        
        # 验证是否为目标版本
        assert current_version == target_version, f"PySide6版本不匹配: {current_version} != {target_version}"
    
    def test_numpy_version_compatibility(self):
        """测试numpy版本兼容性"""
        import numpy as np
        
        current_version = version.parse(np.__version__)
        min_required = version.parse("1.24.0")
        max_allowed = version.parse("2.0.0")
        
        print(f"当前numpy版本: {current_version}")
        print(f"版本范围: {min_required} <= version < {max_allowed}")
        
        # 验证版本在允许范围内
        assert current_version >= min_required, f"numpy版本过低: {current_version} < {min_required}"
        assert current_version < max_allowed, f"numpy版本过高: {current_version} >= {max_allowed}"
        
        # 测试关键API可用性
        try:
            # 测试常用API
            arr = np.array([1, 2, 3])
            result = np.mean(arr)
            assert result == 2.0, "numpy基础功能测试失败"
            print("✅ numpy基础功能测试通过")
        except Exception as e:
            pytest.fail(f"numpy API兼容性测试失败: {e}")
    
    def test_ezdxf_integration(self):
        """测试ezdxf集成"""
        import ezdxf
        
        current_version = version.parse(ezdxf.__version__)
        required_version = version.parse("1.4.2")
        
        print(f"当前ezdxf版本: {current_version}")
        print(f"要求版本: {required_version}")
        
        assert current_version == required_version, f"ezdxf版本不匹配: {current_version} != {required_version}"
        
        # 测试基础功能
        try:
            # 创建新的DXF文档
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # 添加一个圆形实体
            msp.add_circle((0, 0), radius=1.0)
            
            # 验证实体创建成功
            entities = list(msp)
            assert len(entities) == 1, "DXF实体创建失败"
            assert entities[0].dxftype() == 'CIRCLE', "DXF实体类型错误"
            
            print("✅ ezdxf基础功能测试通过")
        except Exception as e:
            pytest.fail(f"ezdxf功能测试失败: {e}")
    
    def test_qt_graphics_compatibility(self):
        """测试Qt图形组件兼容性"""
        from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
        from PySide6.QtCore import Qt
        import pyqtgraph as pg
        
        # 创建Qt应用（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        try:
            # 测试基础Qt组件
            scene = QGraphicsScene()
            view = QGraphicsView(scene)
            
            # 测试pyqtgraph集成
            plot_widget = pg.PlotWidget()
            plot_widget.plot([1, 2, 3], [1, 4, 9])
            
            print("✅ Qt图形组件兼容性测试通过")
        except Exception as e:
            pytest.fail(f"Qt图形组件测试失败: {e}")
        finally:
            # 清理资源
            if hasattr(view, 'close'):
                view.close()
            if hasattr(plot_widget, 'close'):
                plot_widget.close()
    
    def test_database_compatibility(self):
        """测试数据库组件兼容性"""
        from sqlalchemy import create_engine, Column, Integer, String
        from sqlalchemy.orm import declarative_base, sessionmaker
        
        try:
            # 创建内存数据库
            engine = create_engine('sqlite:///:memory:', echo=False)
            Base = declarative_base()
            
            # 定义测试模型
            class TestModel(Base):
                __tablename__ = 'test'
                id = Column(Integer, primary_key=True)
                name = Column(String(50))
            
            # 创建表
            Base.metadata.create_all(engine)
            
            # 测试会话
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # 插入测试数据
            test_obj = TestModel(name='test')
            session.add(test_obj)
            session.commit()
            
            # 查询测试
            result = session.query(TestModel).first()
            assert result.name == 'test', "数据库操作失败"
            
            session.close()
            print("✅ 数据库兼容性测试通过")
        except Exception as e:
            pytest.fail(f"数据库兼容性测试失败: {e}")
    
    def test_no_version_conflicts(self):
        """测试无版本冲突警告"""
        # 捕获警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # 导入所有关键模块
            import PySide6
            import numpy
            import ezdxf
            import pyqtgraph
            import matplotlib
            import scipy
            
            # 检查是否有版本冲突警告
            version_warnings = [warning for warning in w 
                              if 'version' in str(warning.message).lower() 
                              or 'conflict' in str(warning.message).lower()]
            
            if version_warnings:
                for warning in version_warnings:
                    print(f"⚠️ 版本警告: {warning.message}")
            
            # 允许一些非关键警告，但不应有严重冲突
            critical_warnings = [w for w in version_warnings 
                                if 'critical' in str(w.message).lower() 
                                or 'error' in str(w.message).lower()]
            
            assert len(critical_warnings) == 0, f"发现关键版本冲突: {critical_warnings}"
            print("✅ 无关键版本冲突")
    
    def test_memory_usage_baseline(self):
        """测试内存使用基线"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 导入所有依赖
        import PySide6
        import numpy
        import ezdxf
        import pyqtgraph
        import matplotlib
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 内存增长应该在合理范围内（<500MB）
        assert memory_increase < 500, f"内存使用过高: {memory_increase:.2f} MB"
        print("✅ 内存使用在合理范围内")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
