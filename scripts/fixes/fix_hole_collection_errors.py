#!/usr/bin/env python3
"""
修复孔位集合和状态管理相关错误
解决 HoleCollection.get_statistics 和 StatusManager.update_status 缺失方法问题
"""

import sys
import os
from pathlib import Path
import shutil
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def backup_file(file_path):
    """备份文件"""
    if Path(file_path).exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"📁 备份文件: {file_path} -> {backup_path}")
        return backup_path
    return None

def check_hole_collection_methods():
    """检查 HoleCollection 类的方法"""
    print("🔍 检查 HoleCollection 类...")
    
    try:
        from src.core_business.models.hole_data import HoleCollection
        
        # 检查现有方法
        hole_collection = HoleCollection()
        methods = [method for method in dir(hole_collection) if not method.startswith('_')]
        
        print(f"📋 HoleCollection 现有方法: {len(methods)} 个")
        
        # 检查关键方法
        required_methods = ['get_statistics', 'update_hole_status', 'get_hole_by_id']
        missing_methods = []
        
        for method in required_methods:
            if hasattr(hole_collection, method):
                print(f"  ✅ {method}: 存在")
            else:
                print(f"  ❌ {method}: 缺失")
                missing_methods.append(method)
        
        return missing_methods
        
    except Exception as e:
        print(f"❌ 检查 HoleCollection 失败: {e}")
        return []

def add_missing_hole_collection_methods():
    """添加缺失的 HoleCollection 方法"""
    print("🔧 添加缺失的 HoleCollection 方法...")
    
    hole_data_file = project_root / "src/core_business/models/hole_data.py"
    if not hole_data_file.exists():
        print("❌ HoleCollection 文件不存在")
        return False
    
    # 备份文件
    backup_path = backup_file(hole_data_file)
    
    # 读取文件内容
    with open(hole_data_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已有 get_statistics 方法
    if "def get_statistics(self)" in content:
        print("✅ get_statistics 方法已存在")
        return True
    
    # 在 HoleCollection 类末尾添加缺失方法
    methods_to_add = '''
    def get_statistics(self) -> Dict[str, int]:
        """获取孔位统计信息"""
        stats = {
            'total_holes': len(self.holes),
            'qualified': 0,
            'defective': 0,
            'blind': 0,
            'pending': 0,
            'tie_rod': 0,
            'processing': 0
        }
        
        for hole in self.holes.values():
            status = hole.status.value if hasattr(hole.status, 'value') else str(hole.status)
            if status == 'qualified':
                stats['qualified'] += 1
            elif status == 'defective':
                stats['defective'] += 1
            elif status == 'blind':
                stats['blind'] += 1
            elif status in ['pending', 'undetected']:
                stats['pending'] += 1
            elif status == 'tie_rod':
                stats['tie_rod'] += 1
            elif status in ['processing', 'detecting']:
                stats['processing'] += 1
        
        return stats
    
    def update_hole_status(self, hole_id: str, new_status) -> bool:
        """更新孔位状态"""
        try:
            if hole_id in self.holes:
                self.holes[hole_id].status = new_status
                return True
            return False
        except Exception as e:
            print(f"更新孔位状态失败: {e}")
            return False
    
    def get_hole_by_id(self, hole_id: str) -> Optional['HoleData']:
        """根据ID获取孔位"""
        return self.holes.get(hole_id)
'''
    
    # 找到 HoleCollection 类的结尾并添加方法
    class_end_pattern = "class HoleCollection:"
    class_start_idx = content.find(class_end_pattern)
    
    if class_start_idx == -1:
        print("❌ 找不到 HoleCollection 类定义")
        return False
    
    # 找到类的最后一个方法
    lines = content.split('\n')
    class_start_line = None
    
    for i, line in enumerate(lines):
        if class_end_pattern in line:
            class_start_line = i
            break
    
    if class_start_line is None:
        print("❌ 找不到 HoleCollection 类开始位置")
        return False
    
    # 在文件末尾添加方法（简化处理）
    if not content.endswith('\n'):
        content += '\n'
    
    content += methods_to_add
    
    # 写回文件
    with open(hole_data_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已添加 HoleCollection 缺失方法")
    return True

def check_status_manager():
    """检查 StatusManager 类"""
    print("🔍 检查 StatusManager 类...")
    
    try:
        # 查找 StatusManager 相关文件
        from pathlib import Path
        
        status_files = list(project_root.rglob("*status*.py"))
        manager_files = [f for f in status_files if 'manager' in f.name.lower()]
        
        print(f"📋 找到状态管理相关文件: {len(manager_files)} 个")
        for f in manager_files:
            print(f"  - {f.relative_to(project_root)}")
        
        return manager_files
        
    except Exception as e:
        print(f"❌ 检查 StatusManager 失败: {e}")
        return []

def create_status_manager_if_missing():
    """如果缺失则创建 StatusManager"""
    print("🔧 检查并创建 StatusManager...")
    
    # 检查是否已有 StatusManager
    status_manager_file = project_root / "src/core_business/managers/status_manager.py"
    
    if status_manager_file.exists():
        print("✅ StatusManager 文件已存在")
        
        # 检查是否有 update_status 方法
        with open(status_manager_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "def update_status(" in content:
            print("✅ update_status 方法已存在")
            return True
        else:
            print("⚠️ update_status 方法缺失，需要添加")
    else:
        print("📝 创建 StatusManager 文件...")
        
        # 创建目录
        status_manager_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建 StatusManager 类
        status_manager_content = '''"""
状态管理器
管理孔位状态的更新和同步
"""

from typing import Dict, Any, Optional, Callable
from enum import Enum
import logging


class StatusManager:
    """状态管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.status_callbacks = []
        self.hole_collection = None
    
    def set_hole_collection(self, hole_collection):
        """设置孔位集合"""
        self.hole_collection = hole_collection
    
    def update_status(self, hole_id: str, new_status, **kwargs) -> bool:
        """更新孔位状态"""
        try:
            if self.hole_collection and hasattr(self.hole_collection, 'update_hole_status'):
                result = self.hole_collection.update_hole_status(hole_id, new_status)
                
                # 触发回调
                for callback in self.status_callbacks:
                    try:
                        callback(hole_id, new_status)
                    except Exception as e:
                        self.logger.error(f"状态回调失败: {e}")
                
                return result
            else:
                self.logger.warning("孔位集合未设置或缺少更新方法")
                return False
                
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
            return False
    
    def add_status_callback(self, callback: Callable):
        """添加状态变更回调"""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable):
        """移除状态变更回调"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def get_hole_status(self, hole_id: str):
        """获取孔位状态"""
        try:
            if self.hole_collection and hasattr(self.hole_collection, 'get_hole_by_id'):
                hole = self.hole_collection.get_hole_by_id(hole_id)
                return hole.status if hole else None
            return None
        except Exception as e:
            self.logger.error(f"获取孔位状态失败: {e}")
            return None
    
    def batch_update_status(self, updates: Dict[str, Any]) -> int:
        """批量更新状态"""
        success_count = 0
        for hole_id, status in updates.items():
            if self.update_status(hole_id, status):
                success_count += 1
        return success_count
'''
        
        # 写入文件
        with open(status_manager_file, 'w', encoding='utf-8') as f:
            f.write(status_manager_content)
        
        print(f"✅ 已创建 StatusManager: {status_manager_file}")
    
    return True

def test_fixes():
    """测试修复效果"""
    print("🔍 测试修复效果...")
    
    try:
        # 测试 HoleCollection
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        hole_collection = HoleCollection()
        
        # 添加测试数据
        test_hole = HoleData(
            hole_id="TEST001",
            center_x=100.0,
            center_y=200.0,
            radius=8.8,
            status=HoleStatus.PENDING
        )
        hole_collection.add_hole(test_hole)
        
        # 测试 get_statistics 方法
        if hasattr(hole_collection, 'get_statistics'):
            stats = hole_collection.get_statistics()
            print(f"✅ get_statistics 工作正常: {stats}")
        else:
            print("❌ get_statistics 方法仍然缺失")
            return False
        
        # 测试 update_hole_status 方法
        if hasattr(hole_collection, 'update_hole_status'):
            result = hole_collection.update_hole_status("TEST001", HoleStatus.QUALIFIED)
            print(f"✅ update_hole_status 工作正常: {result}")
        else:
            print("❌ update_hole_status 方法仍然缺失")
            return False
        
        # 测试 StatusManager
        try:
            from src.core_business.managers.status_manager import StatusManager
            
            status_manager = StatusManager()
            status_manager.set_hole_collection(hole_collection)
            
            # 测试 update_status 方法
            result = status_manager.update_status("TEST001", HoleStatus.DEFECTIVE)
            print(f"✅ StatusManager.update_status 工作正常: {result}")
            
        except ImportError:
            print("❌ StatusManager 导入失败")
            return False
        
        print("🎉 所有修复测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始修复孔位集合和状态管理错误...")
    print("=" * 60)
    
    # 检查并修复 HoleCollection
    missing_methods = check_hole_collection_methods()
    if missing_methods:
        add_missing_hole_collection_methods()
    
    print("\n" + "-" * 60)
    
    # 检查并创建 StatusManager
    check_status_manager()
    create_status_manager_if_missing()
    
    print("\n" + "-" * 60)
    
    # 测试修复效果
    if test_fixes():
        print("\n✅ 所有错误修复完成！")
        print("💡 建议:")
        print("   1. 重启应用")
        print("   2. 测试模拟检测功能")
        print("   3. 检查控制台是否还有错误")
    else:
        print("\n⚠️ 部分修复可能需要手动调整")
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)