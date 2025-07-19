"""
缺陷类别管理模块
实现缺陷类别的定义、选择、管理和配置功能
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class DefectCategoryInfo:
    """缺陷类别信息"""
    id: int
    name: str                    # 英文名称
    display_name: str           # 显示名称（中文）
    color: str                  # 颜色代码
    description: str = ""       # 描述
    enabled: bool = True        # 是否启用
    priority: int = 0           # 优先级（用于排序）
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'DefectCategoryInfo':
        """从字典创建"""
        return cls(**data)


class DefectCategoryManager:
    """缺陷类别管理器"""
    
    # 默认缺陷类别定义
    DEFAULT_CATEGORIES = [
        DefectCategoryInfo(
            id=0, 
            name="crack", 
            display_name="裂纹", 
            color="#FF0000",
            description="表面或内部的裂纹缺陷",
            priority=1
        ),
        DefectCategoryInfo(
            id=1, 
            name="corrosion", 
            display_name="腐蚀", 
            color="#FF8000",
            description="由化学反应引起的材料损伤",
            priority=2
        ),
        DefectCategoryInfo(
            id=2, 
            name="pit", 
            display_name="点蚀", 
            color="#FFFF00",
            description="局部的小型腐蚀坑",
            priority=3
        ),
        DefectCategoryInfo(
            id=3, 
            name="scratch", 
            display_name="划痕", 
            color="#00FF00",
            description="表面的机械划伤",
            priority=4
        ),
        DefectCategoryInfo(
            id=4, 
            name="deposit", 
            display_name="沉积物", 
            color="#00FFFF",
            description="表面的异物沉积",
            priority=5
        ),
        DefectCategoryInfo(
            id=5, 
            name="other", 
            display_name="其他", 
            color="#8000FF",
            description="其他类型的缺陷",
            priority=6
        )
    ]
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化缺陷类别管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        self.config_file = config_file or "config/defect_categories.json"
        self.categories: Dict[int, DefectCategoryInfo] = {}
        
        # 加载配置
        self.load_categories()
        
    def load_categories(self):
        """加载缺陷类别配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.categories = {}
                for category_data in data.get('categories', []):
                    category = DefectCategoryInfo.from_dict(category_data)
                    self.categories[category.id] = category
                    
                print(f"从配置文件加载了 {len(self.categories)} 个缺陷类别")
                
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self._load_default_categories()
        else:
            print("配置文件不存在，使用默认类别")
            self._load_default_categories()
            
    def _load_default_categories(self):
        """加载默认缺陷类别"""
        self.categories = {}
        for category in self.DEFAULT_CATEGORIES:
            self.categories[category.id] = category
            
    def save_categories(self) -> bool:
        """保存缺陷类别配置"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 准备保存数据
            data = {
                'version': '1.0',
                'categories': [category.to_dict() for category in self.categories.values()]
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
            
    def get_category(self, category_id: int) -> Optional[DefectCategoryInfo]:
        """获取指定ID的缺陷类别"""
        return self.categories.get(category_id)
        
    def get_all_categories(self, enabled_only: bool = False) -> List[DefectCategoryInfo]:
        """
        获取所有缺陷类别
        
        Args:
            enabled_only: 是否只返回启用的类别
            
        Returns:
            List[DefectCategoryInfo]: 缺陷类别列表
        """
        categories = list(self.categories.values())
        
        if enabled_only:
            categories = [cat for cat in categories if cat.enabled]
            
        # 按优先级排序
        categories.sort(key=lambda x: (x.priority, x.id))
        
        return categories
        
    def get_category_names(self, enabled_only: bool = False) -> List[str]:
        """获取所有类别的显示名称"""
        categories = self.get_all_categories(enabled_only)
        return [cat.display_name for cat in categories]
        
    def get_category_colors(self, enabled_only: bool = False) -> Dict[int, str]:
        """获取所有类别的颜色映射"""
        categories = self.get_all_categories(enabled_only)
        return {cat.id: cat.color for cat in categories}
        
    def get_category_name(self, category_id: int) -> str:
        """获取指定ID的类别显示名称"""
        category = self.get_category(category_id)
        return category.display_name if category else f"未知类别{category_id}"
        
    def get_category_color(self, category_id: int) -> str:
        """获取指定ID的类别颜色"""
        category = self.get_category(category_id)
        return category.color if category else "#808080"
        
    def get_category_by_name(self, name: str) -> Optional[DefectCategoryInfo]:
        """根据名称查找类别"""
        for category in self.categories.values():
            if category.name == name or category.display_name == name:
                return category
        return None
        
    def add_category(self, category: DefectCategoryInfo) -> bool:
        """
        添加新的缺陷类别
        
        Args:
            category: 缺陷类别信息
            
        Returns:
            bool: 添加是否成功
        """
        if category.id in self.categories:
            print(f"类别ID {category.id} 已存在")
            return False
            
        # 检查名称是否重复
        for existing_category in self.categories.values():
            if (existing_category.name == category.name or 
                existing_category.display_name == category.display_name):
                print(f"类别名称 '{category.name}' 或 '{category.display_name}' 已存在")
                return False
                
        self.categories[category.id] = category
        return True
        
    def update_category(self, category_id: int, **kwargs) -> bool:
        """
        更新缺陷类别信息
        
        Args:
            category_id: 类别ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        if category_id not in self.categories:
            print(f"类别ID {category_id} 不存在")
            return False
            
        category = self.categories[category_id]
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
            else:
                print(f"未知字段: {key}")
                return False
                
        return True
        
    def remove_category(self, category_id: int) -> bool:
        """
        移除缺陷类别
        
        Args:
            category_id: 类别ID
            
        Returns:
            bool: 移除是否成功
        """
        if category_id not in self.categories:
            print(f"类别ID {category_id} 不存在")
            return False
            
        del self.categories[category_id]
        return True
        
    def enable_category(self, category_id: int, enabled: bool = True) -> bool:
        """
        启用或禁用缺陷类别
        
        Args:
            category_id: 类别ID
            enabled: 是否启用
            
        Returns:
            bool: 操作是否成功
        """
        return self.update_category(category_id, enabled=enabled)
        
    def get_next_available_id(self) -> int:
        """获取下一个可用的类别ID"""
        if not self.categories:
            return 0
        return max(self.categories.keys()) + 1
        
    def validate_category_id(self, category_id: int) -> bool:
        """验证类别ID是否有效"""
        return category_id in self.categories and self.categories[category_id].enabled
        
    def get_statistics(self) -> Dict:
        """获取类别统计信息"""
        total_categories = len(self.categories)
        enabled_categories = len([cat for cat in self.categories.values() if cat.enabled])
        
        return {
            'total_categories': total_categories,
            'enabled_categories': enabled_categories,
            'disabled_categories': total_categories - enabled_categories,
            'category_list': [
                {
                    'id': cat.id,
                    'name': cat.display_name,
                    'enabled': cat.enabled,
                    'priority': cat.priority
                }
                for cat in self.get_all_categories()
            ]
        }
        
    def export_categories(self, file_path: str) -> bool:
        """
        导出类别配置到文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            data = {
                'version': '1.0',
                'exported_at': str(Path().cwd()),
                'categories': [category.to_dict() for category in self.categories.values()]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"导出类别配置失败: {e}")
            return False
            
    def import_categories(self, file_path: str, merge: bool = False) -> bool:
        """
        从文件导入类别配置
        
        Args:
            file_path: 导入文件路径
            merge: 是否合并到现有配置（False表示替换）
            
        Returns:
            bool: 导入是否成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not merge:
                self.categories.clear()
                
            for category_data in data.get('categories', []):
                category = DefectCategoryInfo.from_dict(category_data)
                
                if merge and category.id in self.categories:
                    print(f"跳过重复的类别ID: {category.id}")
                    continue
                    
                self.categories[category.id] = category
                
            return True
            
        except Exception as e:
            print(f"导入类别配置失败: {e}")
            return False
            
    def reset_to_default(self):
        """重置为默认类别配置"""
        self._load_default_categories()
        
    def create_ui_combo_items(self, enabled_only: bool = True) -> List[Tuple[str, int]]:
        """
        创建用于UI下拉菜单的项目列表
        
        Args:
            enabled_only: 是否只包含启用的类别
            
        Returns:
            List[Tuple[str, int]]: (显示文本, 类别ID) 的列表
        """
        categories = self.get_all_categories(enabled_only)
        return [(f"{cat.id} - {cat.display_name}", cat.id) for cat in categories]


# 全局缺陷类别管理器实例
_global_category_manager = None

def get_category_manager() -> DefectCategoryManager:
    """获取全局缺陷类别管理器实例"""
    global _global_category_manager
    if _global_category_manager is None:
        _global_category_manager = DefectCategoryManager()
    return _global_category_manager


if __name__ == "__main__":
    # 简单测试
    print("🏷️ 缺陷类别管理器测试")
    print("=" * 50)
    
    manager = DefectCategoryManager()
    
    # 显示所有类别
    categories = manager.get_all_categories()
    print(f"📋 缺陷类别列表 ({len(categories)} 个):")
    for cat in categories:
        status = "✅" if cat.enabled else "❌"
        print(f"  {status} {cat.id}: {cat.display_name} ({cat.name}) - {cat.color}")
        
    # 显示统计信息
    stats = manager.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"  总类别数: {stats['total_categories']}")
    print(f"  启用类别: {stats['enabled_categories']}")
    print(f"  禁用类别: {stats['disabled_categories']}")
    
    # 测试UI项目创建
    ui_items = manager.create_ui_combo_items()
    print(f"\n🖥️ UI下拉菜单项目:")
    for text, value in ui_items:
        print(f"  {text} -> {value}")
