#!/usr/bin/env python3
"""
测试标注检测修复
验证has_annotations方法是否正确检测到标注
"""

import sys
import os
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def test_annotation_detection_fix():
    """测试标注检测修复"""
    print("🔧 测试标注检测修复")
    print("=" * 40)
    
    try:
        from modules.yolo_file_manager import YOLOFileManager
        
        # 测试已知的标注文件
        test_image_path = "Data/H00001/BISDM/result/2-7.0.png"
        test_annotation_path = "Data/H00001/BISDM/result/2-7.0.txt"
        
        print(f"📷 测试图像: {test_image_path}")
        print(f"📝 标注文件: {test_annotation_path}")
        
        # 检查文件是否存在
        if not os.path.exists(test_image_path):
            print(f"❌ 图像文件不存在")
            return False
            
        if not os.path.exists(test_annotation_path):
            print(f"❌ 标注文件不存在")
            return False
            
        print(f"✅ 文件存在检查通过")
        
        # 检查标注文件内容
        with open(test_annotation_path, 'r') as f:
            content = f.read()
            
        print(f"📄 标注文件内容:")
        for i, line in enumerate(content.split('\n')[:10], 1):
            if line.strip():
                print(f"  {i}: {line}")
        
        # 测试has_annotations方法
        has_annotations = YOLOFileManager.has_annotations(test_image_path)
        print(f"\n🔍 has_annotations() 结果: {has_annotations}")
        
        if has_annotations:
            print(f"✅ 标注检测成功!")
            
            # 测试load_annotations方法
            annotations = YOLOFileManager.load_annotations(test_annotation_path)
            print(f"📊 加载的标注数量: {len(annotations)}")
            
            for i, annotation in enumerate(annotations):
                print(f"  标注 {i+1}: 类别={annotation.defect_class}, "
                      f"中心=({annotation.x_center:.3f}, {annotation.y_center:.3f}), "
                      f"大小=({annotation.width:.3f}, {annotation.height:.3f})")
            
            return True
        else:
            print(f"❌ 标注检测失败!")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_archive_functionality():
    """测试归档功能"""
    print("\n📦 测试归档功能")
    print("=" * 40)
    
    try:
        from modules.image_scanner import ImageScanner
        from modules.yolo_file_manager import YOLOFileManager
        
        # 初始化组件
        image_scanner = ImageScanner("Data")
        yolo_manager = YOLOFileManager()
        
        # 扫描图像
        if not image_scanner.scan_directories():
            print("❌ 图像扫描失败")
            return False
            
        print("✅ 图像扫描成功")
        
        # 检查H00001孔位
        hole_id = "H00001"
        images = image_scanner.get_images_for_hole(hole_id)
        
        print(f"🔍 检查孔位: {hole_id}")
        print(f"📄 图像数量: {len(images)}")
        
        annotated_count = 0
        total_annotations = 0
        
        for image_info in images:
            if yolo_manager.has_annotations(image_info.file_path):
                annotated_count += 1
                
                annotation_file = yolo_manager.get_annotation_file_path(image_info.file_path)
                annotations = yolo_manager.load_annotations(annotation_file)
                total_annotations += len(annotations)
                
                print(f"  ✅ {image_info.file_name}: {len(annotations)} 个标注")
            else:
                print(f"  ❌ {image_info.file_name}: 无标注")
        
        print(f"\n📊 统计结果:")
        print(f"  有标注图像: {annotated_count}/{len(images)}")
        print(f"  总标注数: {total_annotations}")
        
        if annotated_count > 0:
            print(f"🎉 检测到标注数据! 归档功能应该正常工作")
            return True
        else:
            print(f"⚠️ 没有检测到标注数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试归档功能时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 标注检测修复测试")
    print("=" * 50)
    
    # 测试1: 标注检测修复
    test1_result = test_annotation_detection_fix()
    
    # 测试2: 归档功能
    test2_result = test_archive_functionality()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    if test1_result and test2_result:
        print("🎉 所有测试通过!")
        print("\n✅ 修复内容:")
        print("   • has_annotations() 方法现在正确检测有效标注行")
        print("   • 忽略注释行和空行")
        print("   • 归档功能应该能正确检测到您的标注")
        
        print("\n🚀 现在您可以:")
        print("   1. 重新运行主程序")
        print("   2. 保存标注时选择'是'进行归档")
        print("   3. 系统将正确检测到您的标注数据")
        
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        
        if not test1_result:
            print("   • 标注检测仍有问题")
        if not test2_result:
            print("   • 归档功能检测有问题")
            
        sys.exit(1)
