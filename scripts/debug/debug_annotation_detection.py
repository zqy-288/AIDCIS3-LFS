#!/usr/bin/env python3
"""
调试标注检测问题
检查为什么系统检测不到已保存的标注
"""

import sys
import os
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def debug_annotation_detection():
    """调试标注检测"""
    print("🔍 调试标注检测问题")
    print("=" * 50)
    
    try:
        from modules.image_scanner import ImageScanner
        from modules.yolo_file_manager import YOLOFileManager
        
        # 初始化组件
        image_scanner = ImageScanner("Data")
        yolo_manager = YOLOFileManager()
        
        # 扫描图像
        if not image_scanner.scan_directories():
            print("❌ 图像扫描失败")
            return
            
        print("✅ 图像扫描成功")
        
        # 检查所有孔位
        hole_ids = image_scanner.get_hole_ids()
        print(f"📁 找到孔位: {hole_ids}")
        
        for hole_id in hole_ids:
            print(f"\n🔍 检查孔位: {hole_id}")
            
            images = image_scanner.get_images_for_hole(hole_id)
            print(f"  📄 图像数量: {len(images)}")
            
            for i, image_info in enumerate(images):
                print(f"  📷 图像 {i+1}: {image_info.file_name}")
                print(f"    📂 路径: {image_info.file_path}")
                
                # 检查图像文件是否存在
                if os.path.exists(image_info.file_path):
                    print(f"    ✅ 图像文件存在")
                else:
                    print(f"    ❌ 图像文件不存在")
                    continue
                
                # 获取标注文件路径
                annotation_file = yolo_manager.get_annotation_file_path(image_info.file_path)
                print(f"    📝 标注文件: {annotation_file}")
                
                # 检查标注文件是否存在
                if os.path.exists(annotation_file):
                    print(f"    ✅ 标注文件存在")
                    
                    # 读取标注内容
                    try:
                        with open(annotation_file, 'r') as f:
                            content = f.read().strip()
                            
                        if content:
                            lines = content.split('\n')
                            print(f"    📊 标注行数: {len(lines)}")
                            
                            # 显示前几行内容
                            for j, line in enumerate(lines[:3]):
                                print(f"      {j+1}: {line}")
                            if len(lines) > 3:
                                print(f"      ... 还有 {len(lines) - 3} 行")
                                
                            # 使用YOLO管理器加载标注
                            annotations = yolo_manager.load_annotations(annotation_file)
                            print(f"    🎯 解析标注: {len(annotations)} 个")
                            
                            # 检查has_annotations方法
                            has_annotations = yolo_manager.has_annotations(image_info.file_path)
                            print(f"    🔍 has_annotations(): {has_annotations}")
                            
                        else:
                            print(f"    ⚠️ 标注文件为空")
                            
                    except Exception as e:
                        print(f"    ❌ 读取标注文件失败: {e}")
                        
                else:
                    print(f"    ❌ 标注文件不存在")
                    
                print()  # 空行分隔
        
        # 总结检查结果
        print("\n" + "=" * 50)
        print("📊 检查总结")
        print("=" * 50)
        
        total_images = 0
        annotated_images = 0
        total_annotations = 0
        
        for hole_id in hole_ids:
            images = image_scanner.get_images_for_hole(hole_id)
            total_images += len(images)
            
            hole_annotated = 0
            hole_annotations = 0
            
            for image_info in images:
                if yolo_manager.has_annotations(image_info.file_path):
                    hole_annotated += 1
                    annotated_images += 1
                    
                    annotation_file = yolo_manager.get_annotation_file_path(image_info.file_path)
                    annotations = yolo_manager.load_annotations(annotation_file)
                    hole_annotations += len(annotations)
                    total_annotations += len(annotations)
            
            if hole_annotated > 0:
                print(f"✅ {hole_id}: {hole_annotated}/{len(images)} 张图像有标注，共 {hole_annotations} 个标注")
            else:
                print(f"❌ {hole_id}: 没有标注")
        
        print(f"\n📈 总计:")
        print(f"  总图像: {total_images}")
        print(f"  有标注图像: {annotated_images}")
        print(f"  总标注数: {total_annotations}")
        print(f"  标注率: {annotated_images/max(total_images, 1)*100:.1f}%")
        
        if annotated_images > 0:
            print(f"\n🎉 检测到标注数据！系统应该能够正常归档。")
            return True
        else:
            print(f"\n⚠️ 没有检测到标注数据。请检查：")
            print(f"   1. 是否已经保存标注？")
            print(f"   2. 标注文件是否在正确位置？")
            print(f"   3. 标注文件格式是否正确？")
            return False
            
    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_current_directory_structure():
    """检查当前目录结构"""
    print("\n🗂️ 检查目录结构")
    print("=" * 30)
    
    data_path = Path("Data")
    if not data_path.exists():
        print("❌ Data目录不存在")
        return
        
    print("✅ Data目录存在")
    
    # 检查孔位目录
    for hole_dir in data_path.iterdir():
        if hole_dir.is_dir() and hole_dir.name.startswith('H'):
            print(f"📁 {hole_dir.name}/")
            
            result_path = hole_dir / "BISDM" / "result"
            if result_path.exists():
                print(f"  📂 BISDM/result/ ✅")
                
                # 检查文件
                image_files = list(result_path.glob("*.jpg")) + list(result_path.glob("*.png"))
                annotation_files = list(result_path.glob("*.txt"))
                
                print(f"    📷 图像文件: {len(image_files)}")
                print(f"    📝 标注文件: {len(annotation_files)}")
                
                # 显示文件列表
                for img_file in image_files[:3]:
                    print(f"      📷 {img_file.name}")
                    
                    # 检查对应的标注文件
                    txt_file = result_path / (img_file.stem + ".txt")
                    if txt_file.exists():
                        print(f"      📝 {txt_file.name} ✅")
                    else:
                        print(f"      📝 {txt_file.name} ❌")
                        
                if len(image_files) > 3:
                    print(f"      ... 还有 {len(image_files) - 3} 个图像文件")
                    
            else:
                print(f"  📂 BISDM/result/ ❌")

if __name__ == "__main__":
    check_current_directory_structure()
    success = debug_annotation_detection()
    
    if not success:
        print("\n💡 建议:")
        print("   1. 确保已经绘制并保存了标注")
        print("   2. 检查Data/H*/BISDM/result/目录下是否有.txt文件")
        print("   3. 检查.txt文件内容是否为YOLO格式")
        print("   4. 重新运行主程序进行标注")
    
    sys.exit(0 if success else 1)
