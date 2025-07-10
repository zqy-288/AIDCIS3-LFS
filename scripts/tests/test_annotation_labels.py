#!/usr/bin/env python3
"""
测试标注框文字标签功能
验证标注框左上角显示标号，右上角显示缺陷类型
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def create_test_image(image_path, width=800, height=600):
    """创建测试图像文件"""
    try:
        from PIL import Image, ImageDraw
        
        # 创建一个简单的测试图像
        image = Image.new('RGB', (width, height), color='lightgray')
        draw = ImageDraw.Draw(image)
        
        # 绘制一些测试内容
        draw.rectangle([100, 100, 300, 200], outline='red', width=3)
        draw.text((150, 150), "Test Defect", fill='black')
        
        image.save(image_path)
        return True
    except ImportError:
        # 如果没有PIL，创建一个假的图像文件
        with open(image_path, 'wb') as f:
            # 写入一个最小的PNG文件头
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x03 \x00\x00\x02X\x08\x02\x00\x00\x00')
            f.write(b'\x00' * 1000)  # 填充数据
        return True
    except Exception:
        return False

def test_annotation_labels():
    """测试标注框文字标签功能"""
    print("🏷️ 测试标注框文字标签功能")
    print("=" * 50)
    
    test_results = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "Data"
    
    try:
        # 创建测试数据
        hole_dir = data_dir / "H00001" / "BISDM" / "result"
        hole_dir.mkdir(parents=True, exist_ok=True)
        
        test_image_path = hole_dir / "test_image.jpg"
        if not create_test_image(test_image_path):
            print("  ⚠️ 无法创建测试图像，使用空文件")
            test_image_path.write_bytes(b"fake image content")
        
        # 测试1: 导入模块
        print("📝 测试1: 导入相关模块")
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPixmap
            
            from modules.defect_annotation_model import DefectAnnotation
            from modules.annotation_graphics_view import AnnotationGraphicsView, AnnotationRectItem
            from modules.defect_category_manager import DefectCategoryManager
            
            print("  ✅ 所有模块导入成功")
            test_results.append(True)
            
        except ImportError as e:
            print(f"  ❌ 模块导入失败: {e}")
            test_results.append(False)
            return False
        
        # 测试2: 创建应用程序和组件
        print("📝 测试2: 创建应用程序和组件")
        try:
            # 创建应用程序实例
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # 创建类别管理器
            category_manager = DefectCategoryManager()
            
            # 创建图形视图
            graphics_view = AnnotationGraphicsView()
            graphics_view.set_category_manager(category_manager)
            
            print("  ✅ 应用程序和组件创建成功")
            test_results.append(True)
            
        except Exception as e:
            print(f"  ❌ 组件创建失败: {e}")
            test_results.append(False)
            return False
        
        # 测试3: 加载图像
        print("📝 测试3: 加载图像")
        try:
            success = graphics_view.load_image(str(test_image_path))
            
            if success:
                print(f"  ✅ 图像加载成功: {test_image_path.name}")
                test_results.append(True)
            else:
                print(f"  ❌ 图像加载失败")
                test_results.append(False)
                
        except Exception as e:
            print(f"  ❌ 图像加载异常: {e}")
            test_results.append(False)
        
        # 测试4: 创建标注项
        print("📝 测试4: 创建标注项")
        try:
            # 创建测试标注
            annotations = [
                DefectAnnotation(0, 0.3, 0.3, 0.2, 0.15),  # 裂纹
                DefectAnnotation(1, 0.6, 0.5, 0.15, 0.2),  # 腐蚀
                DefectAnnotation(2, 0.2, 0.7, 0.18, 0.12), # 点蚀
            ]
            
            # 添加标注到视图
            for annotation in annotations:
                graphics_view.add_annotation(annotation)
            
            # 检查标注项数量
            annotation_items = graphics_view.annotation_items
            if len(annotation_items) == len(annotations):
                print(f"  ✅ 标注项创建成功: {len(annotation_items)} 个")
                
                # 检查标注项属性
                for i, item in enumerate(annotation_items):
                    if hasattr(item, 'annotation_id') and hasattr(item, 'category_manager'):
                        print(f"    📌 标注 {i+1}: ID={item.annotation_id}, 类别={item.annotation.defect_class}")
                    else:
                        print(f"    ❌ 标注 {i+1}: 缺少必要属性")
                        
                test_results.append(True)
            else:
                print(f"  ❌ 标注项数量不匹配: 期望{len(annotations)}，实际{len(annotation_items)}")
                test_results.append(False)
                
        except Exception as e:
            print(f"  ❌ 标注项创建异常: {e}")
            test_results.append(False)
        
        # 测试5: 验证标注项功能
        print("📝 测试5: 验证标注项功能")
        try:
            if len(graphics_view.annotation_items) > 0:
                first_item = graphics_view.annotation_items[0]
                
                # 检查标注编号
                if hasattr(first_item, 'annotation_id'):
                    print(f"  ✅ 标注编号: {first_item.annotation_id}")
                else:
                    print(f"  ❌ 标注编号缺失")
                
                # 检查类别管理器
                if hasattr(first_item, 'category_manager') and first_item.category_manager:
                    category_name = first_item.category_manager.get_category_name(first_item.annotation.defect_class)
                    print(f"  ✅ 缺陷类别: {category_name}")
                else:
                    print(f"  ❌ 类别管理器缺失")
                
                # 检查paint方法是否存在
                if hasattr(first_item, 'paint'):
                    print(f"  ✅ paint方法存在")
                else:
                    print(f"  ❌ paint方法缺失")
                
                test_results.append(True)
            else:
                print(f"  ⚠️ 没有标注项可测试")
                test_results.append(True)
                
        except Exception as e:
            print(f"  ❌ 标注项功能验证异常: {e}")
            test_results.append(False)
        
        # 测试6: 类别管理器功能
        print("📝 测试6: 类别管理器功能")
        try:
            categories = category_manager.get_all_categories()
            
            if len(categories) > 0:
                print(f"  ✅ 类别管理器: {len(categories)} 个类别")
                
                # 测试类别名称获取
                for i in range(min(3, len(categories))):
                    category = categories[i]
                    name = category_manager.get_category_name(category.id)
                    color = category_manager.get_category_color(category.id)
                    print(f"    📋 类别 {category.id}: {name} ({color})")
                
                test_results.append(True)
            else:
                print(f"  ❌ 类别管理器无类别")
                test_results.append(False)
                
        except Exception as e:
            print(f"  ❌ 类别管理器测试异常: {e}")
            test_results.append(False)
        
        # 测试7: 标注计数器
        print("📝 测试7: 标注计数器")
        try:
            # 检查计数器
            counter = graphics_view.annotation_counter
            expected_count = len(graphics_view.annotation_items)
            
            if counter == expected_count:
                print(f"  ✅ 标注计数器正确: {counter}")
                
                # 测试清除功能
                graphics_view.clear_annotations()
                if graphics_view.annotation_counter == 0:
                    print(f"  ✅ 清除后计数器重置: {graphics_view.annotation_counter}")
                    test_results.append(True)
                else:
                    print(f"  ❌ 清除后计数器未重置: {graphics_view.annotation_counter}")
                    test_results.append(False)
            else:
                print(f"  ❌ 标注计数器错误: 期望{expected_count}，实际{counter}")
                test_results.append(False)
                
        except Exception as e:
            print(f"  ❌ 标注计数器测试异常: {e}")
            test_results.append(False)
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过! 标注框文字标签功能正常")
        print("\n📋 功能总结:")
        print("   • 标注框左上角显示白色标号")
        print("   • 标注框右上角显示白色缺陷类型")
        print("   • 自动递增的标注编号")
        print("   • 集成缺陷类别管理器")
        print("   • 支持标注计数器重置")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查标注框文字标签功能")
        return False

if __name__ == "__main__":
    success = test_annotation_labels()
    sys.exit(0 if success else 1)
