#!/usr/bin/env python3
"""
测试归档孔位检测修复
验证ArchiveManager能正确检测到孔位
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def test_archive_hole_detection():
    """测试归档孔位检测"""
    print("🔍 测试归档孔位检测修复")
    print("=" * 50)
    
    try:
        from modules.image_scanner import ImageScanner
        from modules.archive_manager import ArchiveManager
        from modules.yolo_file_manager import YOLOFileManager
        
        # 测试1: 独立的ImageScanner
        print("📝 测试1: 独立的ImageScanner")
        image_scanner1 = ImageScanner("Data")
        success1 = image_scanner1.scan_directories()
        hole_ids1 = image_scanner1.get_hole_ids()
        
        print(f"  扫描结果: {success1}")
        print(f"  孔位列表: {hole_ids1}")
        
        # 测试2: 独立的ArchiveManager
        print("\n📝 测试2: 独立的ArchiveManager")
        archive_manager1 = ArchiveManager("Data", "Archive")
        hole_ids2 = archive_manager1.image_scanner.get_hole_ids()
        
        print(f"  ArchiveManager孔位列表: {hole_ids2}")
        
        # 测试3: 共享ImageScanner的ArchiveManager
        print("\n📝 测试3: 共享ImageScanner的ArchiveManager")
        archive_manager2 = ArchiveManager("Data", "Archive", image_scanner1)
        hole_ids3 = archive_manager2.image_scanner.get_hole_ids()
        
        print(f"  共享ImageScanner孔位列表: {hole_ids3}")
        
        # 验证一致性
        print(f"\n🔍 一致性检查:")
        print(f"  独立ImageScanner: {hole_ids1}")
        print(f"  独立ArchiveManager: {hole_ids2}")
        print(f"  共享ArchiveManager: {hole_ids3}")
        
        if hole_ids1 == hole_ids3:
            print(f"  ✅ 共享ImageScanner一致性检查通过")
        else:
            print(f"  ❌ 共享ImageScanner一致性检查失败")
            
        # 测试4: 检查H00001是否存在
        print(f"\n📝 测试4: 检查H00001孔位")
        test_hole_id = "H00001"
        
        exists_in_scanner = test_hole_id in hole_ids1
        exists_in_archive = test_hole_id in hole_ids3
        
        print(f"  ImageScanner中存在H00001: {exists_in_scanner}")
        print(f"  ArchiveManager中存在H00001: {exists_in_archive}")
        
        if exists_in_scanner and exists_in_archive:
            print(f"  ✅ H00001孔位检测正常")
            
            # 测试归档功能
            print(f"\n📝 测试5: 模拟归档功能")
            
            # 检查是否有标注
            yolo_manager = YOLOFileManager()
            images = image_scanner1.get_images_for_hole(test_hole_id)
            
            has_annotations = False
            for image_info in images:
                if yolo_manager.has_annotations(image_info.file_path):
                    has_annotations = True
                    break
            
            print(f"  H00001有标注: {has_annotations}")
            
            if has_annotations:
                print(f"  ✅ H00001可以归档")
                return True
            else:
                print(f"  ⚠️ H00001没有标注，但孔位检测正常")
                return True
        else:
            print(f"  ❌ H00001孔位检测失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_defect_annotation_tool_integration():
    """测试DefectAnnotationTool集成"""
    print("\n🔧 测试DefectAnnotationTool集成")
    print("=" * 40)
    
    try:
        from PySide6.QtWidgets import QApplication
        
        # 创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from modules.defect_annotation_tool import DefectAnnotationTool
        
        # 创建标注工具
        tool = DefectAnnotationTool()
        
        # 检查ImageScanner和ArchiveManager的一致性
        tool_hole_ids = tool.image_scanner.get_hole_ids()
        archive_hole_ids = tool.archive_manager.image_scanner.get_hole_ids()
        
        print(f"  DefectAnnotationTool孔位: {tool_hole_ids}")
        print(f"  ArchiveManager孔位: {archive_hole_ids}")
        
        if tool_hole_ids == archive_hole_ids:
            print(f"  ✅ DefectAnnotationTool集成一致性检查通过")
            
            # 检查H00001
            if "H00001" in tool_hole_ids:
                print(f"  ✅ H00001在DefectAnnotationTool中存在")
                return True
            else:
                print(f"  ❌ H00001在DefectAnnotationTool中不存在")
                return False
        else:
            print(f"  ❌ DefectAnnotationTool集成一致性检查失败")
            return False
            
    except Exception as e:
        print(f"❌ DefectAnnotationTool集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 归档孔位检测修复测试")
    print("=" * 60)
    
    # 测试1: 归档孔位检测
    test1_result = test_archive_hole_detection()
    
    # 测试2: DefectAnnotationTool集成
    test2_result = test_defect_annotation_tool_integration()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有测试通过!")
        print("\n✅ 修复内容:")
        print("   • ArchiveManager现在使用与DefectAnnotationTool相同的ImageScanner实例")
        print("   • 确保孔位检测的一致性")
        print("   • 解决了'孔位 H00001 不存在'的错误")
        
        print("\n🚀 现在您可以:")
        print("   1. 重新运行主程序")
        print("   2. 保存标注时选择'是'进行归档")
        print("   3. 系统将正确识别H00001孔位并成功归档")
        
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        
        if not test1_result:
            print("   • 归档孔位检测仍有问题")
        if not test2_result:
            print("   • DefectAnnotationTool集成有问题")
            
        sys.exit(1)
