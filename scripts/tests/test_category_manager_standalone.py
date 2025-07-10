#!/usr/bin/env python3
"""
独立的缺陷类别管理器测试
验证缺陷类别的定义、管理和配置功能
"""

import sys
import os
import tempfile
import shutil
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

# 模拟DefectCategoryInfo类
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

# 模拟DefectCategoryManager类
class MockDefectCategoryManager:
    """模拟的缺陷类别管理器"""
    
    # 默认缺陷类别定义
    DEFAULT_CATEGORIES = [
        DefectCategoryInfo(
            id=0, name="crack", display_name="裂纹", color="#FF0000",
            description="表面或内部的裂纹缺陷", priority=1
        ),
        DefectCategoryInfo(
            id=1, name="corrosion", display_name="腐蚀", color="#FF8000",
            description="由化学反应引起的材料损伤", priority=2
        ),
        DefectCategoryInfo(
            id=2, name="pit", display_name="点蚀", color="#FFFF00",
            description="局部的小型腐蚀坑", priority=3
        ),
        DefectCategoryInfo(
            id=3, name="scratch", display_name="划痕", color="#00FF00",
            description="表面的机械划伤", priority=4
        ),
        DefectCategoryInfo(
            id=4, name="deposit", display_name="沉积物", color="#00FFFF",
            description="表面的异物沉积", priority=5
        ),
        DefectCategoryInfo(
            id=5, name="other", display_name="其他", color="#8000FF",
            description="其他类型的缺陷", priority=6
        )
    ]
    
    def __init__(self, config_file=None):
        """初始化缺陷类别管理器"""
        self.config_file = config_file or "config/defect_categories.json"
        self.categories = {}
        
        # 加载默认配置
        self._load_default_categories()
        
    def _load_default_categories(self):
        """加载默认缺陷类别"""
        self.categories = {}
        for category in self.DEFAULT_CATEGORIES:
            self.categories[category.id] = category
            
    def get_category(self, category_id):
        """获取指定ID的缺陷类别"""
        return self.categories.get(category_id)
        
    def get_all_categories(self, enabled_only=False):
        """获取所有缺陷类别"""
        categories = list(self.categories.values())
        
        if enabled_only:
            categories = [cat for cat in categories if cat.enabled]
            
        # 按优先级排序
        categories.sort(key=lambda x: (x.priority, x.id))
        
        return categories
        
    def get_category_name(self, category_id):
        """获取指定ID的类别显示名称"""
        category = self.get_category(category_id)
        return category.display_name if category else f"未知类别{category_id}"
        
    def get_category_color(self, category_id):
        """获取指定ID的类别颜色"""
        category = self.get_category(category_id)
        return category.color if category else "#808080"
        
    def get_category_by_name(self, name):
        """根据名称查找类别"""
        for category in self.categories.values():
            if category.name == name or category.display_name == name:
                return category
        return None
        
    def add_category(self, category):
        """添加新的缺陷类别"""
        if category.id in self.categories:
            return False
            
        # 检查名称是否重复
        for existing_category in self.categories.values():
            if (existing_category.name == category.name or 
                existing_category.display_name == category.display_name):
                return False
                
        self.categories[category.id] = category
        return True
        
    def update_category(self, category_id, **kwargs):
        """更新缺陷类别信息"""
        if category_id not in self.categories:
            return False
            
        category = self.categories[category_id]
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
            else:
                return False
                
        return True
        
    def remove_category(self, category_id):
        """移除缺陷类别"""
        if category_id not in self.categories:
            return False
            
        del self.categories[category_id]
        return True
        
    def enable_category(self, category_id, enabled=True):
        """启用或禁用缺陷类别"""
        return self.update_category(category_id, enabled=enabled)
        
    def get_next_available_id(self):
        """获取下一个可用的类别ID"""
        if not self.categories:
            return 0
        return max(self.categories.keys()) + 1
        
    def validate_category_id(self, category_id):
        """验证类别ID是否有效"""
        return category_id in self.categories and self.categories[category_id].enabled
        
    def get_statistics(self):
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
        
    def save_categories(self):
        """保存缺陷类别配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
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
            
    def create_ui_combo_items(self, enabled_only=True):
        """创建用于UI下拉菜单的项目列表"""
        categories = self.get_all_categories(enabled_only)
        return [(f"{cat.id} - {cat.display_name}", cat.id) for cat in categories]


def test_category_manager():
    """测试缺陷类别管理器功能"""
    print("🏷️ 缺陷类别管理器功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    config_file = os.path.join(temp_dir, "test_categories.json")
    
    try:
        # 测试1: 创建管理器
        print("📝 测试1: 创建类别管理器")
        try:
            manager = MockDefectCategoryManager(config_file)
            
            categories = manager.get_all_categories()
            if len(categories) > 0:
                print(f"  ✅ 管理器创建成功，加载了 {len(categories)} 个默认类别")
                test_results.append(True)
            else:
                print(f"  ❌ 管理器创建失败，没有加载类别")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 管理器创建异常: {e}")
            test_results.append(False)
        
        # 测试2: 获取类别信息
        print("📝 测试2: 获取类别信息")
        try:
            # 获取存在的类别
            category = manager.get_category(0)
            name = manager.get_category_name(0)
            color = manager.get_category_color(0)
            
            if (category is not None and 
                isinstance(name, str) and 
                isinstance(color, str) and color.startswith('#')):
                print(f"  ✅ 类别信息获取成功: {name} ({color})")
                
                # 获取不存在的类别
                unknown_name = manager.get_category_name(999)
                unknown_color = manager.get_category_color(999)
                
                if "未知类别" in unknown_name and unknown_color == "#808080":
                    print(f"  ✅ 未知类别处理正确: {unknown_name} ({unknown_color})")
                    test_results.append(True)
                else:
                    print(f"  ❌ 未知类别处理错误")
                    test_results.append(False)
            else:
                print(f"  ❌ 类别信息获取失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 获取类别信息异常: {e}")
            test_results.append(False)
        
        # 测试3: 按名称查找类别
        print("📝 测试3: 按名称查找类别")
        try:
            # 按英文名称查找
            category_en = manager.get_category_by_name("crack")
            # 按中文名称查找
            category_cn = manager.get_category_by_name("裂纹")
            # 查找不存在的名称
            category_none = manager.get_category_by_name("不存在的类别")
            
            if (category_en is not None and category_en.name == "crack" and
                category_cn is not None and category_cn.display_name == "裂纹" and
                category_none is None):
                print(f"  ✅ 按名称查找类别成功")
                test_results.append(True)
            else:
                print(f"  ❌ 按名称查找类别失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 按名称查找类别异常: {e}")
            test_results.append(False)
        
        # 测试4: 添加自定义类别
        print("📝 测试4: 添加自定义类别")
        try:
            # 添加新类别
            new_category = DefectCategoryInfo(
                id=100,
                name="test_defect",
                display_name="测试缺陷",
                color="#123456",
                description="测试用缺陷类别",
                priority=10
            )
            
            success = manager.add_category(new_category)
            
            if success:
                retrieved = manager.get_category(100)
                if (retrieved is not None and 
                    retrieved.name == "test_defect" and
                    retrieved.display_name == "测试缺陷"):
                    print(f"  ✅ 添加自定义类别成功: {retrieved.display_name}")
                    
                    # 尝试添加重复ID
                    duplicate = DefectCategoryInfo(
                        id=100, name="duplicate", display_name="重复", color="#FFFFFF"
                    )
                    duplicate_success = manager.add_category(duplicate)
                    
                    if not duplicate_success:
                        print(f"  ✅ 重复ID检查正确")
                        test_results.append(True)
                    else:
                        print(f"  ❌ 重复ID检查失败")
                        test_results.append(False)
                else:
                    print(f"  ❌ 添加的类别信息不正确")
                    test_results.append(False)
            else:
                print(f"  ❌ 添加自定义类别失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 添加自定义类别异常: {e}")
            test_results.append(False)
        
        # 测试5: 更新和删除类别
        print("📝 测试5: 更新和删除类别")
        try:
            # 更新类别
            update_success = manager.update_category(100, display_name="更新的测试缺陷", color="#654321")
            
            if update_success:
                updated_category = manager.get_category(100)
                if (updated_category.display_name == "更新的测试缺陷" and
                    updated_category.color == "#654321"):
                    print(f"  ✅ 类别更新成功: {updated_category.display_name}")
                    
                    # 删除类别
                    delete_success = manager.remove_category(100)
                    
                    if delete_success and manager.get_category(100) is None:
                        print(f"  ✅ 类别删除成功")
                        test_results.append(True)
                    else:
                        print(f"  ❌ 类别删除失败")
                        test_results.append(False)
                else:
                    print(f"  ❌ 类别更新信息不正确")
                    test_results.append(False)
            else:
                print(f"  ❌ 类别更新失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 更新和删除类别异常: {e}")
            test_results.append(False)
        
        # 测试6: 启用/禁用类别
        print("📝 测试6: 启用/禁用类别")
        try:
            # 禁用类别
            disable_success = manager.enable_category(0, False)
            
            if disable_success:
                category = manager.get_category(0)
                if not category.enabled:
                    print(f"  ✅ 类别禁用成功")
                    
                    # 验证ID有效性检查
                    is_valid = manager.validate_category_id(0)
                    if not is_valid:
                        print(f"  ✅ 禁用类别ID验证正确")
                        
                        # 重新启用
                        enable_success = manager.enable_category(0, True)
                        if enable_success and manager.validate_category_id(0):
                            print(f"  ✅ 类别重新启用成功")
                            test_results.append(True)
                        else:
                            print(f"  ❌ 类别重新启用失败")
                            test_results.append(False)
                    else:
                        print(f"  ❌ 禁用类别ID验证错误")
                        test_results.append(False)
                else:
                    print(f"  ❌ 类别禁用失败")
                    test_results.append(False)
            else:
                print(f"  ❌ 禁用类别操作失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 启用/禁用类别异常: {e}")
            test_results.append(False)
        
        # 测试7: 统计信息
        print("📝 测试7: 统计信息")
        try:
            stats = manager.get_statistics()
            
            if (isinstance(stats, dict) and
                'total_categories' in stats and
                'enabled_categories' in stats and
                'disabled_categories' in stats and
                'category_list' in stats):
                print(f"  ✅ 统计信息结构正确:")
                print(f"    总类别数: {stats['total_categories']}")
                print(f"    启用类别: {stats['enabled_categories']}")
                print(f"    禁用类别: {stats['disabled_categories']}")
                
                # 验证数值一致性
                if (stats['total_categories'] == 
                    stats['enabled_categories'] + stats['disabled_categories']):
                    print(f"  ✅ 统计数值一致性正确")
                    test_results.append(True)
                else:
                    print(f"  ❌ 统计数值一致性错误")
                    test_results.append(False)
            else:
                print(f"  ❌ 统计信息结构错误")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 统计信息异常: {e}")
            test_results.append(False)
        
        # 测试8: UI组件支持
        print("📝 测试8: UI组件支持")
        try:
            ui_items = manager.create_ui_combo_items(enabled_only=True)
            
            if (isinstance(ui_items, list) and len(ui_items) > 0):
                print(f"  ✅ UI下拉菜单项目创建成功: {len(ui_items)} 个项目")
                
                # 验证项目格式
                all_valid = True
                for text, value in ui_items:
                    if not (isinstance(text, str) and isinstance(value, int) and " - " in text):
                        all_valid = False
                        break
                        
                if all_valid:
                    print(f"  ✅ UI项目格式正确")
                    # 显示前几个项目
                    for i, (text, value) in enumerate(ui_items[:3]):
                        print(f"    {i+1}. {text} -> {value}")
                    test_results.append(True)
                else:
                    print(f"  ❌ UI项目格式错误")
                    test_results.append(False)
            else:
                print(f"  ❌ UI下拉菜单项目创建失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ UI组件支持异常: {e}")
            test_results.append(False)
        
        # 测试9: 配置保存
        print("📝 测试9: 配置保存")
        try:
            save_success = manager.save_categories()
            
            if save_success and os.path.exists(config_file):
                file_size = os.path.getsize(config_file)
                print(f"  ✅ 配置保存成功: {config_file} ({file_size} 字节)")
                
                # 验证文件内容
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if ('version' in data and 'categories' in data and
                    isinstance(data['categories'], list)):
                    print(f"  ✅ 配置文件格式正确")
                    test_results.append(True)
                else:
                    print(f"  ❌ 配置文件格式错误")
                    test_results.append(False)
            else:
                print(f"  ❌ 配置保存失败")
                test_results.append(False)
        except Exception as e:
            print(f"  ❌ 配置保存异常: {e}")
            test_results.append(False)
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过! 缺陷类别管理器功能正常")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = test_category_manager()
    sys.exit(0 if success else 1)
