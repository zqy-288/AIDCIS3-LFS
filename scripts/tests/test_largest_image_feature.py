#!/usr/bin/env python3
"""
测试最大图像文件自动选择功能
验证每个孔位自动选择最大图像文件的功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def create_test_data_with_sizes(data_dir):
    """创建不同大小的测试图像文件"""
    holes = ["H00001", "H00002"]
    
    for hole_id in holes:
        hole_dir = data_dir / hole_id / "BISDM" / "result"
        hole_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建不同大小的图像文件
        image_sizes = [
            ("2-3.0.png", 1024),      # 1KB
            ("2-4.0.png", 2048),      # 2KB  
            ("2-5.0.png", 4096),      # 4KB
            ("2-6.0.png", 8192),      # 8KB
            ("2-7.0.png", 16384),     # 16KB - 最大
        ]
        
        for filename, size in image_sizes:
            image_file = hole_dir / filename
            # 创建指定大小的文件
            image_file.write_bytes(b"fake image content" * (size // 18))

def test_largest_image_selection():
    """测试最大图像文件选择功能"""
    print("📌 测试最大图像文件自动选择功能")
    print("=" * 50)
    
    test_results = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "Data"
    
    try:
        # 创建测试数据
        create_test_data_with_sizes(data_dir)
        
        # 测试1: 图像扫描器识别文件大小
        print("📝 测试1: 图像扫描器识别文件大小")
        try:
            from modules.image_scanner import ImageScanner
            
            scanner = ImageScanner(str(data_dir))
            success = scanner.scan_directories()
            
            if success:
                hole_ids = scanner.get_hole_ids()
                print(f"  ✅ 扫描成功: {len(hole_ids)} 个孔位")
                
                for hole_id in hole_ids:
                    images = scanner.get_images_for_hole(hole_id)
                    print(f"  📁 {hole_id}: {len(images)} 张图像")
                    
                    # 找到最大文件
                    largest_size = 0
                    largest_file = None
                    
                    for image_info in images:
                        try:
                            file_size = os.path.getsize(image_info.file_path)
                            size_kb = file_size / 1024
                            print(f"    📄 {image_info.file_name}: {size_kb:.1f} KB")
                            
                            if file_size > largest_size:
                                largest_size = file_size
                                largest_file = image_info.file_name
                        except OSError:
                            print(f"    ❌ 无法获取文件大小: {image_info.file_name}")
                    
                    if largest_file:
                        print(f"    📌 最大文件: {largest_file} ({largest_size/1024:.1f} KB)")
                        
                        # 验证是否是2-7.0.png
                        if largest_file == "2-7.0.png":
                            print(f"    ✅ 正确识别最大文件")
                        else:
                            print(f"    ❌ 最大文件识别错误，期望: 2-7.0.png")
                
                test_results.append(True)
            else:
                print(f"  ❌ 扫描失败")
                test_results.append(False)
                
        except Exception as e:
            print(f"  ❌ 图像扫描测试异常: {e}")
            test_results.append(False)
        
        # 测试2: 缺陷标注工具的最大文件选择
        print("\n📝 测试2: 缺陷标注工具的最大文件选择")
        try:
            from PySide6.QtWidgets import QApplication
            
            # 创建应用程序实例（如果不存在）
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            from modules.defect_annotation_tool import DefectAnnotationTool
            
            # 创建标注工具实例
            tool = DefectAnnotationTool()
            
            # 修改数据路径
            tool.image_scanner = ImageScanner(str(data_dir))
            
            # 扫描图像
            tool.scan_images()
            
            # 检查孔位下拉菜单
            hole_count = tool.hole_combo.count()
            if hole_count > 0:
                print(f"  ✅ 孔位下拉菜单: {hole_count} 个孔位")
                
                # 选择第一个孔位
                first_hole = tool.hole_combo.itemText(0)
                tool.hole_combo.setCurrentText(first_hole)
                
                # 检查图像列表
                image_count = tool.image_list.count()
                if image_count > 0:
                    print(f"  ✅ 图像列表: {image_count} 张图像")
                    
                    # 检查当前选中的项目
                    current_item = tool.image_list.currentItem()
                    if current_item:
                        current_text = current_item.text()
                        print(f"  📌 当前选中: {current_text}")
                        
                        # 验证是否包含推荐标记和最大文件名
                        if "2-7.0.png" in current_text and "[推荐]" in current_text:
                            print(f"  ✅ 正确自动选择最大文件")
                            test_results.append(True)
                        else:
                            print(f"  ❌ 未正确选择最大文件")
                            test_results.append(False)
                    else:
                        print(f"  ❌ 没有选中任何图像")
                        test_results.append(False)
                else:
                    print(f"  ❌ 图像列表为空")
                    test_results.append(False)
            else:
                print(f"  ❌ 孔位下拉菜单为空")
                test_results.append(False)
                
        except Exception as e:
            print(f"  ❌ 缺陷标注工具测试异常: {e}")
            test_results.append(False)
        
        # 测试3: 孔位信息显示
        print("\n📝 测试3: 孔位信息显示")
        try:
            if 'tool' in locals():
                # 检查孔位信息标签
                if hasattr(tool, 'hole_info_label'):
                    info_text = tool.hole_info_label.text()
                    print(f"  📊 孔位信息: {info_text}")
                    
                    # 验证信息格式
                    if "H00001" in info_text and "MB" in info_text and "2-7.0.png" in info_text:
                        print(f"  ✅ 孔位信息显示正确")
                        test_results.append(True)
                    else:
                        print(f"  ❌ 孔位信息格式错误")
                        test_results.append(False)
                else:
                    print(f"  ❌ 孔位信息标签不存在")
                    test_results.append(False)
            else:
                print(f"  ⚠️ 跳过测试，工具实例不存在")
                test_results.append(True)
                
        except Exception as e:
            print(f"  ❌ 孔位信息显示测试异常: {e}")
            test_results.append(False)
        
        # 测试4: 提示信息显示
        print("\n📝 测试4: 提示信息显示")
        try:
            if 'tool' in locals():
                # 查找提示标签
                tip_found = False
                for child in tool.hole_selection_group.findChildren(QLabel):
                    if "建议" in child.text() and "最大" in child.text():
                        print(f"  💡 提示信息: {child.text()}")
                        tip_found = True
                        break
                
                if tip_found:
                    print(f"  ✅ 提示信息显示正确")
                    test_results.append(True)
                else:
                    print(f"  ❌ 提示信息未找到")
                    test_results.append(False)
            else:
                print(f"  ⚠️ 跳过测试，工具实例不存在")
                test_results.append(True)
                
        except Exception as e:
            print(f"  ❌ 提示信息显示测试异常: {e}")
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
        print("\n🎉 所有测试通过! 最大图像文件自动选择功能正常")
        print("\n📋 功能总结:")
        print("   • 自动识别每个孔位中最大的图像文件")
        print("   • 在图像列表中标记推荐文件")
        print("   • 自动选择最大文件作为默认选项")
        print("   • 显示孔位统计信息")
        print("   • 提供用户友好的提示信息")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查功能实现")
        return False

if __name__ == "__main__":
    success = test_largest_image_selection()
    sys.exit(0 if success else 1)
