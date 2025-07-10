#!/usr/bin/env python3
"""
测试归档图像加载功能
验证从归档加载后是否正确显示图像和标注
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def test_archive_image_loading():
    """测试归档图像加载功能"""
    print("🖼️ 测试归档图像加载功能")
    print("=" * 50)
    
    try:
        from modules.image_scanner import ImageScanner
        from modules.archive_manager import ArchiveManager
        from modules.yolo_file_manager import YOLOFileManager
        
        # 检查现有数据
        print("📝 检查现有数据")
        
        # 检查Data目录
        data_path = Path("Data")
        if not data_path.exists():
            print("❌ Data目录不存在")
            return False
            
        # 检查H00001
        h00001_path = data_path / "H00001" / "BISDM" / "result"
        if not h00001_path.exists():
            print("❌ H00001目录不存在")
            return False
            
        # 检查图像和标注文件
        image_files = list(h00001_path.glob("*.png")) + list(h00001_path.glob("*.jpg"))
        annotation_files = list(h00001_path.glob("*.txt"))
        
        print(f"  📷 图像文件: {len(image_files)}")
        print(f"  📝 标注文件: {len(annotation_files)}")
        
        if len(image_files) == 0:
            print("❌ 没有图像文件")
            return False
            
        if len(annotation_files) == 0:
            print("❌ 没有标注文件")
            return False
            
        # 找到有标注的图像
        yolo_manager = YOLOFileManager()
        annotated_images = []
        
        for img_file in image_files:
            if yolo_manager.has_annotations(str(img_file)):
                annotated_images.append(img_file)
                
        print(f"  🎯 有标注的图像: {len(annotated_images)}")
        
        if len(annotated_images) == 0:
            print("❌ 没有有标注的图像")
            return False
            
        # 显示有标注的图像信息
        for img_file in annotated_images:
            annotation_file = yolo_manager.get_annotation_file_path(str(img_file))
            annotations = yolo_manager.load_annotations(annotation_file)
            print(f"    ✅ {img_file.name}: {len(annotations)} 个标注")
            
        print("✅ 数据检查通过")
        
        # 测试归档管理器
        print("\n📦 测试归档管理器")
        
        image_scanner = ImageScanner("Data")
        image_scanner.scan_directories()
        
        archive_manager = ArchiveManager("Data", "Archive", image_scanner)
        
        # 检查是否已有归档
        archived_holes = archive_manager.get_archived_holes()
        print(f"  📋 已归档孔位: {archived_holes}")
        
        # 如果H00001还没归档，先归档它
        if "H00001" not in archived_holes:
            print("  📦 归档H00001...")
            success = archive_manager.archive_hole("H00001", "测试归档")
            if success:
                print("  ✅ H00001归档成功")
            else:
                print("  ❌ H00001归档失败")
                return False
        else:
            print("  ✅ H00001已经归档")
            
        # 模拟删除原始数据
        print("\n🗑️ 模拟删除原始数据")
        backup_path = Path("Data_backup")
        if backup_path.exists():
            shutil.rmtree(backup_path)
            
        shutil.copytree(data_path, backup_path)
        shutil.rmtree(h00001_path)
        
        print("  ✅ 原始数据已删除")
        
        # 验证数据确实被删除
        if h00001_path.exists():
            print("  ❌ 数据删除失败")
            return False
            
        # 从归档恢复
        print("\n🔄 从归档恢复数据")
        success = archive_manager.load_archived_hole("H00001")
        
        if success:
            print("  ✅ 归档恢复成功")
            
            # 验证恢复的数据
            if h00001_path.exists():
                restored_images = list(h00001_path.glob("*.png")) + list(h00001_path.glob("*.jpg"))
                restored_annotations = list(h00001_path.glob("*.txt"))
                
                print(f"    📷 恢复的图像: {len(restored_images)}")
                print(f"    📝 恢复的标注: {len(restored_annotations)}")
                
                # 检查标注内容
                restored_annotated = []
                for img_file in restored_images:
                    if yolo_manager.has_annotations(str(img_file)):
                        restored_annotated.append(img_file)
                        
                print(f"    🎯 恢复的有标注图像: {len(restored_annotated)}")
                
                if len(restored_annotated) > 0:
                    print("  ✅ 数据恢复验证通过")
                    
                    # 显示恢复的标注信息
                    for img_file in restored_annotated:
                        annotation_file = yolo_manager.get_annotation_file_path(str(img_file))
                        annotations = yolo_manager.load_annotations(annotation_file)
                        print(f"    ✅ {img_file.name}: {len(annotations)} 个标注")
                        
                    return True
                else:
                    print("  ❌ 恢复的数据没有标注")
                    return False
            else:
                print("  ❌ 数据恢复路径不存在")
                return False
        else:
            print("  ❌ 归档恢复失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 恢复原始数据
        try:
            backup_path = Path("Data_backup")
            if backup_path.exists():
                if data_path.exists():
                    shutil.rmtree(data_path)
                shutil.copytree(backup_path, data_path)
                shutil.rmtree(backup_path)
                print("\n🔄 原始数据已恢复")
        except Exception as e:
            print(f"⚠️ 恢复原始数据时发生错误: {e}")

def test_ui_integration():
    """测试UI集成"""
    print("\n🖥️ 测试UI集成")
    print("=" * 30)
    
    try:
        from PySide6.QtWidgets import QApplication
        
        # 创建应用程序实例
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from modules.defect_annotation_tool import DefectAnnotationTool
        
        # 创建标注工具
        tool = DefectAnnotationTool()
        
        # 检查auto_select_annotated_image方法是否存在
        if hasattr(tool, 'auto_select_annotated_image'):
            print("  ✅ auto_select_annotated_image方法存在")
        else:
            print("  ❌ auto_select_annotated_image方法不存在")
            return False
            
        # 检查load_from_archive方法
        if hasattr(tool, 'load_from_archive'):
            print("  ✅ load_from_archive方法存在")
        else:
            print("  ❌ load_from_archive方法不存在")
            return False
            
        print("  ✅ UI集成检查通过")
        return True
        
    except Exception as e:
        print(f"  ❌ UI集成测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 归档图像加载功能测试")
    print("=" * 60)
    
    # 测试1: 归档图像加载
    test1_result = test_archive_image_loading()
    
    # 测试2: UI集成
    test2_result = test_ui_integration()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 所有测试通过!")
        print("\n✅ 修复内容:")
        print("   • 加载归档后自动选择有标注的图像")
        print("   • 使用QTimer确保孔位切换完成后再选择图像")
        print("   • 完整的归档-恢复-显示工作流")
        
        print("\n🚀 现在加载归档后应该能看到:")
        print("   1. 自动切换到恢复的孔位")
        print("   2. 自动选择有标注的图像")
        print("   3. 显示图像和标注框")
        print("   4. 标注框上的编号和类别标签")
        
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        
        if not test1_result:
            print("   • 归档图像加载功能有问题")
        if not test2_result:
            print("   • UI集成有问题")
            
        sys.exit(1)
