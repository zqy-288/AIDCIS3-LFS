"""
系统集成测试
测试整个缺陷标注工具系统的端到端功能
"""

import unittest
import tempfile
import os
import shutil
import json
from pathlib import Path
from modules.defect_annotation_model import DefectAnnotation
from modules.image_scanner import ImageScanner
from modules.yolo_file_manager import YOLOFileManager
from modules.defect_category_manager import DefectCategoryManager
from modules.archive_manager import ArchiveManager


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "Data"
        self.archive_dir = Path(self.temp_dir) / "Archive"
        self.config_dir = Path(self.temp_dir) / "config"
        
        # 创建完整的测试数据集
        self.create_comprehensive_test_data()
        
        # 初始化系统组件
        self.initialize_system_components()
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_comprehensive_test_data(self):
        """创建全面的测试数据集"""
        # 创建多个孔位，模拟真实项目结构
        holes_data = {
            "H00001": {"images": 5, "annotated": 3},
            "H00002": {"images": 4, "annotated": 4},
            "H00003": {"images": 6, "annotated": 2},
            "H00004": {"images": 3, "annotated": 0},  # 无标注孔位
            "H00005": {"images": 7, "annotated": 5}
        }
        
        for hole_id, data in holes_data.items():
            hole_dir = self.data_dir / hole_id / "BISDM" / "result"
            hole_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建图像文件
            for i in range(data["images"]):
                image_file = hole_dir / f"image_{i+1:03d}.jpg"
                # 创建不同大小的假图像文件
                content_size = 1024 * (i + 1)  # 不同大小
                image_file.write_bytes(b"fake image content" * (content_size // 18))
                
            # 创建标注文件
            for i in range(data["annotated"]):
                annotation_file = hole_dir / f"image_{i+1:03d}.txt"
                
                # 创建多样化的标注数据
                annotations = []
                num_annotations = (i % 3) + 1  # 1-3个标注
                
                for j in range(num_annotations):
                    annotation = DefectAnnotation(
                        defect_class=j % 6,  # 使用不同的缺陷类别
                        x_center=0.2 + j * 0.2,
                        y_center=0.3 + j * 0.15,
                        width=0.1 + j * 0.05,
                        height=0.12 + j * 0.03
                    )
                    annotations.append(annotation)
                    
                # 保存标注
                YOLOFileManager.save_annotations(annotations, str(annotation_file))
                
    def initialize_system_components(self):
        """初始化系统组件"""
        self.image_scanner = ImageScanner(str(self.data_dir))
        self.yolo_manager = YOLOFileManager()
        self.category_manager = DefectCategoryManager(str(self.config_dir / "categories.json"))
        self.archive_manager = ArchiveManager(str(self.data_dir), str(self.archive_dir))
        
    def test_complete_system_workflow(self):
        """测试完整的系统工作流"""
        print("\n🔄 执行完整系统工作流测试")
        
        # 阶段1: 项目初始化和数据扫描
        print("📂 阶段1: 项目初始化和数据扫描")
        
        # 扫描项目数据
        scan_success = self.image_scanner.scan_directories()
        self.assertTrue(scan_success, "项目数据扫描失败")
        
        # 获取项目统计
        scan_stats = self.image_scanner.get_statistics()
        print(f"  发现孔位: {scan_stats['total_holes']}")
        print(f"  总图像: {scan_stats['total_images']}")
        print(f"  图像大小: {scan_stats['total_size_mb']} MB")
        
        self.assertGreater(scan_stats['total_holes'], 0)
        self.assertGreater(scan_stats['total_images'], 0)
        
        # 阶段2: 缺陷类别配置
        print("🏷️ 阶段2: 缺陷类别配置")
        
        # 验证默认类别
        categories = self.category_manager.get_all_categories()
        print(f"  可用缺陷类别: {len(categories)}")
        
        self.assertGreaterEqual(len(categories), 6)  # 至少6个默认类别
        
        # 保存类别配置
        config_saved = self.category_manager.save_categories()
        self.assertTrue(config_saved, "类别配置保存失败")
        
        # 阶段3: 标注数据验证和处理
        print("📝 阶段3: 标注数据验证和处理")
        
        # 验证现有标注文件
        annotation_files = self.yolo_manager.find_annotation_files(str(self.data_dir))
        print(f"  发现标注文件: {len(annotation_files)}")
        
        valid_files = 0
        invalid_files = 0
        
        for annotation_file in annotation_files:
            is_valid, errors = self.yolo_manager.validate_annotation_file(annotation_file)
            if is_valid:
                valid_files += 1
            else:
                invalid_files += 1
                print(f"  无效标注文件: {annotation_file}")
                
        print(f"  有效标注文件: {valid_files}")
        print(f"  无效标注文件: {invalid_files}")
        
        self.assertGreater(valid_files, 0)
        
        # 阶段4: 标注统计分析
        print("📊 阶段4: 标注统计分析")
        
        annotation_stats = self.yolo_manager.get_annotation_statistics(str(self.data_dir))
        print(f"  总标注数: {annotation_stats['total_annotations']}")
        print(f"  按类别分布: {annotation_stats['annotations_by_class']}")
        
        self.assertGreater(annotation_stats['total_annotations'], 0)
        
        # 阶段5: 归档管理
        print("📦 阶段5: 归档管理")
        
        # 获取有标注的孔位
        annotated_holes = self.archive_manager.get_annotated_holes()
        print(f"  有标注的孔位: {annotated_holes}")
        
        self.assertGreater(len(annotated_holes), 0)
        
        # 归档前两个孔位
        archived_count = 0
        for hole_id in annotated_holes[:2]:
            summary = self.archive_manager.get_hole_annotation_summary(hole_id)
            success = self.archive_manager.archive_hole(
                hole_id, 
                f"系统测试归档 - {summary['total_annotations']}个标注"
            )
            if success:
                archived_count += 1
                print(f"  归档成功: {hole_id}")
                
        self.assertGreater(archived_count, 0)
        
        # 阶段6: 数据恢复验证
        print("🔄 阶段6: 数据恢复验证")
        
        # 选择一个已归档的孔位进行恢复测试
        archived_holes = self.archive_manager.get_archived_holes()
        if archived_holes:
            test_hole = archived_holes[0]
            
            # 备份原始路径
            original_path = self.data_dir / test_hole
            backup_path = Path(self.temp_dir) / f"backup_{test_hole}"
            
            if original_path.exists():
                shutil.copytree(original_path, backup_path)
                shutil.rmtree(original_path)
                
            # 从归档恢复
            restore_success = self.archive_manager.load_archived_hole(test_hole)
            self.assertTrue(restore_success, f"恢复孔位 {test_hole} 失败")
            
            # 验证恢复的数据
            self.assertTrue(original_path.exists(), "恢复的孔位目录不存在")
            
            # 重新扫描验证
            self.image_scanner.scan_directories()
            restored_images = self.image_scanner.get_images_for_hole(test_hole)
            self.assertGreater(len(restored_images), 0, "恢复的图像文件为空")
            
            print(f"  恢复验证成功: {test_hole}")
            
        # 阶段7: 系统状态报告
        print("📋 阶段7: 系统状态报告")
        
        # 生成综合报告
        final_stats = self.generate_system_report()
        print(f"  系统报告生成完成")
        
        # 验证报告内容
        self.assertIn('scan_statistics', final_stats)
        self.assertIn('annotation_statistics', final_stats)
        self.assertIn('archive_statistics', final_stats)
        self.assertIn('category_statistics', final_stats)
        
        print("✅ 完整系统工作流测试通过")
        
    def test_multi_user_scenario(self):
        """测试多用户场景"""
        print("\n👥 执行多用户场景测试")
        
        # 模拟用户A的工作
        print("👤 用户A: 标注孔位H00001")
        hole_a = "H00001"
        images_a = self.image_scanner.get_images_for_hole(hole_a)
        
        for i, image_info in enumerate(images_a[:2]):
            annotations = [DefectAnnotation(0, 0.3 + i*0.1, 0.4 + i*0.1, 0.15, 0.2)]
            annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
            self.yolo_manager.save_annotations(annotations, annotation_file)
            
        # 模拟用户B的工作
        print("👤 用户B: 标注孔位H00002")
        hole_b = "H00002"
        images_b = self.image_scanner.get_images_for_hole(hole_b)
        
        for i, image_info in enumerate(images_b[:3]):
            annotations = [DefectAnnotation(1, 0.6 + i*0.05, 0.5 + i*0.05, 0.12, 0.18)]
            annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
            self.yolo_manager.save_annotations(annotations, annotation_file)
            
        # 验证工作不冲突
        summary_a = self.archive_manager.get_hole_annotation_summary(hole_a)
        summary_b = self.archive_manager.get_hole_annotation_summary(hole_b)
        
        self.assertGreater(summary_a['total_annotations'], 0)
        self.assertGreater(summary_b['total_annotations'], 0)
        
        # 模拟管理员归档
        print("👨‍💼 管理员: 归档完成的工作")
        archive_success_a = self.archive_manager.archive_hole(hole_a, "用户A完成")
        archive_success_b = self.archive_manager.archive_hole(hole_b, "用户B完成")
        
        self.assertTrue(archive_success_a)
        self.assertTrue(archive_success_b)
        
        print("✅ 多用户场景测试通过")
        
    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        print("\n⚡ 执行大数据集性能测试")
        
        # 创建大量标注数据
        large_hole = "H00005"
        images = self.image_scanner.get_images_for_hole(large_hole)
        
        total_annotations = 0
        for image_info in images:
            # 每张图像创建多个标注
            annotations = []
            for i in range(10):  # 每张图像10个标注
                annotation = DefectAnnotation(
                    defect_class=i % 6,
                    x_center=0.1 + (i % 3) * 0.3,
                    y_center=0.1 + (i // 3) * 0.3,
                    width=0.08,
                    height=0.1
                )
                annotations.append(annotation)
                
            annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
            success = self.yolo_manager.save_annotations(annotations, annotation_file)
            self.assertTrue(success)
            
            total_annotations += len(annotations)
            
        print(f"  创建了 {total_annotations} 个标注")
        
        # 测试批量加载性能
        all_image_paths = [img.file_path for img in images]
        load_results = self.yolo_manager.batch_load_annotations(all_image_paths)
        
        loaded_total = sum(len(annotations) for annotations in load_results.values())
        self.assertEqual(loaded_total, total_annotations)
        
        # 测试归档性能
        archive_success = self.archive_manager.archive_hole(large_hole, "大数据集测试")
        self.assertTrue(archive_success)
        
        print(f"  批量处理 {len(images)} 张图像成功")
        print("✅ 大数据集性能测试通过")
        
    def test_error_recovery(self):
        """测试错误恢复能力"""
        print("\n🛠️ 执行错误恢复测试")
        
        # 测试1: 损坏的标注文件恢复
        print("🔧 测试损坏标注文件恢复")
        
        hole_id = "H00003"
        images = self.image_scanner.get_images_for_hole(hole_id)
        
        if images:
            # 创建损坏的标注文件
            corrupted_file = self.yolo_manager.get_annotation_file_path(images[0].file_path)
            with open(corrupted_file, 'w') as f:
                f.write("invalid annotation data\n")
                f.write("0 invalid coordinates\n")
                f.write("not a valid line\n")
                
            # 验证系统能处理损坏文件
            is_valid, errors = self.yolo_manager.validate_annotation_file(corrupted_file)
            self.assertFalse(is_valid)
            self.assertGreater(len(errors), 0)
            
            # 加载时应该跳过无效行
            loaded_annotations = self.yolo_manager.load_annotations(corrupted_file)
            self.assertEqual(len(loaded_annotations), 0)  # 所有行都无效
            
        # 测试2: 部分文件丢失恢复
        print("🔧 测试部分文件丢失恢复")
        
        # 先归档一个孔位
        self.archive_manager.archive_hole(hole_id, "错误恢复测试")
        
        # 删除部分原始文件
        original_path = self.data_dir / hole_id
        if original_path.exists():
            # 只删除部分文件
            result_dir = original_path / "BISDM" / "result"
            if result_dir.exists():
                files = list(result_dir.glob("*.jpg"))
                if files:
                    files[0].unlink()  # 删除第一个图像文件
                    
        # 从归档恢复
        restore_success = self.archive_manager.load_archived_hole(hole_id)
        self.assertTrue(restore_success)
        
        # 验证文件已恢复
        restored_files = list((self.data_dir / hole_id / "BISDM" / "result").glob("*.jpg"))
        self.assertGreater(len(restored_files), 0)
        
        print("✅ 错误恢复测试通过")
        
    def generate_system_report(self) -> dict:
        """生成系统状态报告"""
        # 重新扫描确保数据最新
        self.image_scanner.scan_directories()
        
        report = {
            'timestamp': str(Path().cwd()),
            'scan_statistics': self.image_scanner.get_statistics(),
            'annotation_statistics': self.yolo_manager.get_annotation_statistics(str(self.data_dir)),
            'archive_statistics': self.archive_manager.get_archive_statistics(),
            'category_statistics': self.category_manager.get_statistics()
        }
        
        # 保存报告到文件
        report_file = Path(self.temp_dir) / "system_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        return report
        
    def test_configuration_management(self):
        """测试配置管理"""
        print("\n⚙️ 执行配置管理测试")
        
        # 测试类别配置导出导入
        export_file = Path(self.temp_dir) / "exported_categories.json"
        export_success = self.category_manager.export_categories(str(export_file))
        self.assertTrue(export_success)
        
        # 清空当前配置
        original_count = len(self.category_manager.get_all_categories())
        self.category_manager.categories.clear()
        
        # 导入配置
        import_success = self.category_manager.import_categories(str(export_file))
        self.assertTrue(import_success)
        
        # 验证配置恢复
        restored_count = len(self.category_manager.get_all_categories())
        self.assertEqual(restored_count, original_count)
        
        print("✅ 配置管理测试通过")


class TestSystemRobustness(unittest.TestCase):
    """系统健壮性测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_concurrent_access(self):
        """测试并发访问"""
        # 创建多个组件实例模拟并发访问
        data_dir = Path(self.temp_dir) / "Data"
        
        # 创建测试数据
        hole_dir = data_dir / "H00001" / "BISDM" / "result"
        hole_dir.mkdir(parents=True, exist_ok=True)
        
        image_file = hole_dir / "test.jpg"
        image_file.write_bytes(b"test image")
        
        # 创建多个管理器实例
        manager1 = YOLOFileManager()
        manager2 = YOLOFileManager()
        
        # 同时操作同一文件
        annotation_file = manager1.get_annotation_file_path(str(image_file))
        
        annotations1 = [DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)]
        annotations2 = [DefectAnnotation(1, 0.3, 0.7, 0.1, 0.15)]
        
        # 两个管理器同时保存（后者会覆盖前者）
        success1 = manager1.save_annotations(annotations1, annotation_file)
        success2 = manager2.save_annotations(annotations2, annotation_file)
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # 验证最后的结果
        final_annotations = manager1.load_annotations(annotation_file)
        self.assertEqual(len(final_annotations), 1)
        self.assertEqual(final_annotations[0].defect_class, 1)  # 应该是第二次保存的结果
        
    def test_resource_cleanup(self):
        """测试资源清理"""
        # 创建大量临时文件
        data_dir = Path(self.temp_dir) / "Data"
        
        for i in range(10):
            hole_dir = data_dir / f"H{i:05d}" / "BISDM" / "result"
            hole_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建图像和标注文件
            image_file = hole_dir / "test.jpg"
            annotation_file = hole_dir / "test.txt"
            
            image_file.write_bytes(b"test image" * 100)
            
            annotations = [DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)]
            YOLOFileManager.save_annotations(annotations, str(annotation_file))
            
        # 验证文件创建成功
        scanner = ImageScanner(str(data_dir))
        scanner.scan_directories()
        
        self.assertEqual(len(scanner.get_hole_ids()), 10)
        
        # 清理资源（通过删除目录）
        shutil.rmtree(data_dir)
        
        # 验证清理成功
        self.assertFalse(data_dir.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
