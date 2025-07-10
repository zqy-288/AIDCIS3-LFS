#!/usr/bin/env python3
"""
测试归档加载功能
验证"加载归档"按钮的正确逻辑
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def create_test_data_with_annotations(data_dir):
    """创建带标注的测试数据"""
    holes = ["H00001", "H00002"]
    
    for hole_id in holes:
        hole_dir = data_dir / hole_id / "BISDM" / "result"
        hole_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建图像文件
        for i in range(3):
            image_file = hole_dir / f"image{i+1}.jpg"
            image_file.write_bytes(b"fake image content")
            
            # 创建标注文件
            annotation_file = hole_dir / f"image{i+1}.txt"
            with open(annotation_file, 'w') as f:
                f.write(f"0 0.5 0.5 0.2 0.3\n")  # 一个标注
                f.write(f"1 0.3 0.7 0.1 0.15\n")  # 另一个标注

def test_archive_loading_logic():
    """测试归档加载逻辑"""
    print("📦 测试归档加载功能")
    print("=" * 50)
    
    test_results = []
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "Data"
    archive_dir = Path(temp_dir) / "Archive"
    
    try:
        # 创建测试数据
        create_test_data_with_annotations(data_dir)
        
        # 测试1: 导入模块
        print("📝 测试1: 导入相关模块")
        try:
            from modules.archive_manager import ArchiveManager
            from modules.image_scanner import ImageScanner
            from modules.yolo_file_manager import YOLOFileManager
            
            print("  ✅ 模块导入成功")
            test_results.append(True)
            
        except ImportError as e:
            print(f"  ❌ 模块导入失败: {e}")
            test_results.append(False)
            return False
        
        # 测试2: 创建归档管理器
        print("📝 测试2: 创建归档管理器")
        try:
            archive_manager = ArchiveManager(str(data_dir), str(archive_dir))
            image_scanner = ImageScanner(str(data_dir))
            yolo_manager = YOLOFileManager()
            
            print("  ✅ 归档管理器创建成功")
            test_results.append(True)
            
        except Exception as e:
            print(f"  ❌ 归档管理器创建失败: {e}")
            test_results.append(False)
            return False
        
        # 测试3: 扫描和归档数据
        print("📝 测试3: 扫描和归档数据")
        try:
            # 扫描图像
            image_scanner.scan_directories()
            
            # 获取有标注的孔位
            annotated_holes = archive_manager.get_annotated_holes()
            print(f"  📁 有标注的孔位: {annotated_holes}")
            
            if len(annotated_holes) > 0:
                # 归档第一个孔位
                hole_id = annotated_holes[0]
                success = archive_manager.archive_hole(hole_id, "测试归档")
                
                if success:
                    print(f"  ✅ 孔位 {hole_id} 归档成功")
                    test_results.append(True)
                else:
                    print(f"  ❌ 孔位 {hole_id} 归档失败")
                    test_results.append(False)
            else:
                print("  ⚠️ 没有有标注的孔位")
                test_results.append(True)
                
        except Exception as e:
            print(f"  ❌ 扫描和归档异常: {e}")
            test_results.append(False)
        
        # 测试4: 获取已归档孔位
        print("📝 测试4: 获取已归档孔位")
        try:
            archived_holes = archive_manager.get_archived_holes()
            print(f"  📦 已归档孔位: {archived_holes}")
            
            if len(archived_holes) > 0:
                # 获取归档记录
                hole_id = archived_holes[0]
                record = archive_manager.get_archive_record(hole_id)
                
                if record:
                    print(f"  ✅ 归档记录: {hole_id}")
                    print(f"    📊 总标注: {record.total_annotations}")
                    print(f"    📝 备注: {record.notes}")
                    test_results.append(True)
                else:
                    print(f"  ❌ 无法获取归档记录")
                    test_results.append(False)
            else:
                print("  ⚠️ 没有已归档的孔位")
                test_results.append(True)
                
        except Exception as e:
            print(f"  ❌ 获取已归档孔位异常: {e}")
            test_results.append(False)
        
        # 测试5: 模拟删除原始数据
        print("📝 测试5: 模拟删除原始数据")
        try:
            if archived_holes:
                hole_id = archived_holes[0]
                original_path = data_dir / hole_id
                
                # 备份原始数据
                backup_path = Path(temp_dir) / f"backup_{hole_id}"
                if original_path.exists():
                    shutil.copytree(original_path, backup_path)
                    shutil.rmtree(original_path)
                    print(f"  🗑️ 已删除原始数据: {hole_id}")
                    
                # 验证数据确实被删除
                if not original_path.exists():
                    print(f"  ✅ 原始数据删除确认")
                    test_results.append(True)
                else:
                    print(f"  ❌ 原始数据删除失败")
                    test_results.append(False)
            else:
                print("  ⚠️ 跳过测试，没有已归档孔位")
                test_results.append(True)
                
        except Exception as e:
            print(f"  ❌ 删除原始数据异常: {e}")
            test_results.append(False)
        
        # 测试6: 从归档恢复数据
        print("📝 测试6: 从归档恢复数据")
        try:
            if archived_holes:
                hole_id = archived_holes[0]
                
                # 从归档恢复
                success = archive_manager.load_archived_hole(hole_id)
                
                if success:
                    print(f"  ✅ 从归档恢复成功: {hole_id}")
                    
                    # 验证数据已恢复
                    restored_path = data_dir / hole_id / "BISDM" / "result"
                    if restored_path.exists():
                        image_files = list(restored_path.glob("*.jpg"))
                        annotation_files = list(restored_path.glob("*.txt"))
                        
                        print(f"    📄 恢复图像: {len(image_files)} 个")
                        print(f"    📝 恢复标注: {len(annotation_files)} 个")
                        
                        # 验证标注内容
                        if annotation_files:
                            with open(annotation_files[0], 'r') as f:
                                content = f.read().strip()
                                if content:
                                    print(f"    ✅ 标注内容已恢复")
                                    test_results.append(True)
                                else:
                                    print(f"    ❌ 标注内容为空")
                                    test_results.append(False)
                        else:
                            print(f"    ❌ 没有恢复标注文件")
                            test_results.append(False)
                    else:
                        print(f"    ❌ 恢复路径不存在")
                        test_results.append(False)
                else:
                    print(f"  ❌ 从归档恢复失败")
                    test_results.append(False)
            else:
                print("  ⚠️ 跳过测试，没有已归档孔位")
                test_results.append(True)
                
        except Exception as e:
            print(f"  ❌ 从归档恢复异常: {e}")
            test_results.append(False)
        
        # 测试7: 验证UI组件逻辑
        print("📝 测试7: 验证UI组件逻辑")
        try:
            from PySide6.QtWidgets import QApplication
            
            # 创建应用程序实例
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            from modules.defect_annotation_tool import DefectAnnotationTool
            
            # 创建标注工具
            tool = DefectAnnotationTool()
            
            # 修改数据路径
            tool.archive_manager = ArchiveManager(str(data_dir), str(archive_dir))
            
            # 更新归档列表
            tool.update_archive_list()
            
            # 检查归档下拉菜单
            combo_count = tool.archive_combo.count()
            if combo_count > 1:  # 至少有"选择已归档孔位..."和一个归档项
                print(f"  ✅ 归档下拉菜单: {combo_count} 个选项")
                
                # 检查按钮文本
                button_text = tool.load_btn.text()
                if button_text == "加载归档":
                    print(f"  ✅ 按钮文本正确: {button_text}")
                    test_results.append(True)
                else:
                    print(f"  ❌ 按钮文本错误: {button_text}")
                    test_results.append(False)
            else:
                print(f"  ❌ 归档下拉菜单选项不足: {combo_count}")
                test_results.append(False)
                
        except Exception as e:
            print(f"  ❌ UI组件逻辑验证异常: {e}")
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
        print("\n🎉 所有测试通过! 归档加载功能正常")
        print("\n📋 功能总结:")
        print("   • '已归档标注'下拉菜单显示真正的归档数据")
        print("   • '加载归档'按钮从选中归档恢复数据到原图")
        print("   • 保存标注后可选择归档当前孔位")
        print("   • 支持完整的归档-恢复工作流")
        
        print("\n🚀 使用流程:")
        print("   1. 标注完成后点击'保存标注'")
        print("   2. 选择'是'将孔位归档")
        print("   3. 从'已归档标注'下拉菜单选择归档")
        print("   4. 点击'加载归档'恢复数据到原图")
        
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查归档加载功能")
        return False

if __name__ == "__main__":
    success = test_archive_loading_logic()
    sys.exit(0 if success else 1)
