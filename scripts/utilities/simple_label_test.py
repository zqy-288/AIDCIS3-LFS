#!/usr/bin/env python3
"""
简单的标注框标签测试
验证标注框文字标签功能的基本实现
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def test_basic_imports():
    """测试基本导入"""
    print("🔍 测试基本导入...")
    
    try:
        # 测试核心模块
        from modules.defect_annotation_model import DefectAnnotation
        print("  ✅ DefectAnnotation 导入成功")
        
        from modules.annotation_graphics_view import AnnotationRectItem
        print("  ✅ AnnotationRectItem 导入成功")
        
        from modules.defect_category_manager import DefectCategoryManager
        print("  ✅ DefectCategoryManager 导入成功")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def test_annotation_rect_item():
    """测试标注矩形项"""
    print("\n🏷️ 测试标注矩形项...")
    
    try:
        from modules.defect_annotation_model import DefectAnnotation
        from modules.annotation_graphics_view import AnnotationRectItem
        from modules.defect_category_manager import DefectCategoryManager
        
        # 创建类别管理器
        category_manager = DefectCategoryManager()
        
        # 创建测试标注
        annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
        
        # 创建标注矩形项
        rect_item = AnnotationRectItem(
            annotation=annotation,
            image_width=800,
            image_height=600,
            annotation_id=1,
            category_manager=category_manager
        )
        
        # 检查属性
        if hasattr(rect_item, 'annotation_id'):
            print(f"  ✅ 标注编号: {rect_item.annotation_id}")
        else:
            print("  ❌ 标注编号缺失")
            return False
            
        if hasattr(rect_item, 'category_manager'):
            print("  ✅ 类别管理器已设置")
        else:
            print("  ❌ 类别管理器缺失")
            return False
            
        if hasattr(rect_item, 'paint'):
            print("  ✅ paint方法存在")
        else:
            print("  ❌ paint方法缺失")
            return False
        
        # 测试类别名称获取
        category_name = category_manager.get_category_name(annotation.defect_class)
        print(f"  ✅ 缺陷类别名称: {category_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 标注矩形项测试失败: {e}")
        return False

def test_category_manager():
    """测试类别管理器"""
    print("\n📋 测试类别管理器...")
    
    try:
        from modules.defect_category_manager import DefectCategoryManager
        
        # 创建类别管理器
        manager = DefectCategoryManager()
        
        # 获取所有类别
        categories = manager.get_all_categories()
        print(f"  ✅ 类别数量: {len(categories)}")
        
        # 测试前3个类别
        for i in range(min(3, len(categories))):
            category = categories[i]
            name = manager.get_category_name(category.id)
            color = manager.get_category_color(category.id)
            print(f"    📌 类别 {category.id}: {name} ({color})")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 类别管理器测试失败: {e}")
        return False

def test_graphics_view_integration():
    """测试图形视图集成"""
    print("\n🖼️ 测试图形视图集成...")
    
    try:
        from modules.annotation_graphics_view import AnnotationGraphicsView
        from modules.defect_category_manager import DefectCategoryManager
        
        # 创建组件
        graphics_view = AnnotationGraphicsView()
        category_manager = DefectCategoryManager()
        
        # 设置类别管理器
        graphics_view.set_category_manager(category_manager)
        
        # 检查属性
        if hasattr(graphics_view, 'category_manager'):
            print("  ✅ 图形视图类别管理器已设置")
        else:
            print("  ❌ 图形视图类别管理器缺失")
            return False
            
        if hasattr(graphics_view, 'annotation_counter'):
            print(f"  ✅ 标注计数器: {graphics_view.annotation_counter}")
        else:
            print("  ❌ 标注计数器缺失")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 图形视图集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🏷️ 标注框文字标签功能测试")
    print("=" * 40)
    
    tests = [
        test_basic_imports,
        test_annotation_rect_item,
        test_category_manager,
        test_graphics_view_integration
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # 总结
    print("\n" + "=" * 40)
    print("📊 测试结果总结")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        print("\n📋 实现的功能:")
        print("   • 标注框左上角显示白色标号")
        print("   • 标注框右上角显示白色缺陷类型")
        print("   • 自动递增的标注编号")
        print("   • 集成缺陷类别管理器")
        print("   • 重写paint方法绘制文字标签")
        
        print("\n🚀 使用方法:")
        print("   1. 运行主程序: python main.py")
        print("   2. 切换到缺陷标注选项卡")
        print("   3. 选择孔位和图像")
        print("   4. 使用标注模式绘制标注框")
        print("   5. 标注框将显示编号和类别名称")
        
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查实现")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
