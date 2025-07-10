"""
归档管理器单元测试
"""

import unittest
import tempfile
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from modules.archive_manager import ArchiveManager, ArchiveRecord
from modules.defect_annotation_model import DefectAnnotation
from modules.yolo_file_manager import YOLOFileManager


class TestArchiveRecord(unittest.TestCase):
    """ArchiveRecord测试"""
    
    def test_archive_record_creation(self):
        """测试归档记录创建"""
        record = ArchiveRecord(
            hole_id="H00001",
            archived_at="2024-01-01T12:00:00",
            total_images=10,
            annotated_images=8,
            total_annotations=15,
            annotation_summary={0: 5, 1: 10},
            archive_path="/path/to/archive/H00001",
            notes="测试归档"
        )
        
        self.assertEqual(record.hole_id, "H00001")
        self.assertEqual(record.total_images, 10)
        self.assertEqual(record.annotated_images, 8)
        self.assertEqual(record.total_annotations, 15)
        self.assertEqual(record.notes, "测试归档")
        
    def test_archive_record_to_dict(self):
        """测试归档记录转换为字典"""
        record = ArchiveRecord(
            hole_id="H00002",
            archived_at="2024-01-01T12:00:00",
            total_images=5,
            annotated_images=3,
            total_annotations=8,
            annotation_summary={0: 3, 2: 5},
            archive_path="/path/to/archive/H00002"
        )
        
        record_dict = record.to_dict()
        
        self.assertIsInstance(record_dict, dict)
        self.assertEqual(record_dict['hole_id'], "H00002")
        self.assertEqual(record_dict['total_images'], 5)
        self.assertEqual(record_dict['annotated_images'], 3)
        
    def test_archive_record_from_dict(self):
        """测试从字典创建归档记录"""
        data = {
            'hole_id': "H00003",
            'archived_at': "2024-01-01T12:00:00",
            'total_images': 12,
            'annotated_images': 10,
            'total_annotations': 20,
            'annotation_summary': {0: 8, 1: 12},
            'archive_path': "/path/to/archive/H00003",
            'notes': "从字典创建"
        }
        
        record = ArchiveRecord.from_dict(data)
        
        self.assertEqual(record.hole_id, "H00003")
        self.assertEqual(record.total_images, 12)
        self.assertEqual(record.annotated_images, 10)
        self.assertEqual(record.notes, "从字典创建")


class TestArchiveManager(unittest.TestCase):
    """ArchiveManager测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "Data"
        self.archive_dir = Path(self.temp_dir) / "Archive"
        
        # 创建测试数据结构
        self.create_test_data()
        
        # 创建归档管理器
        self.manager = ArchiveManager(str(self.data_dir), str(self.archive_dir))
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_test_data(self):
        """创建测试数据"""
        # 创建孔位目录结构
        holes = ["H00001", "H00002", "H00003"]
        
        for hole_id in holes:
            hole_dir = self.data_dir / hole_id / "BISDM" / "result"
            hole_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建测试图像文件
            for i in range(3):
                image_file = hole_dir / f"image{i+1}.jpg"
                image_file.write_bytes(b"fake image content")
                
                # 为部分图像创建标注文件
                if i < 2:  # 前两张图像有标注
                    annotation_file = hole_dir / f"image{i+1}.txt"
                    annotations = [
                        DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3),
                        DefectAnnotation(1, 0.3, 0.7, 0.1, 0.15)
                    ]
                    YOLOFileManager.save_annotations(annotations, str(annotation_file))
                    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        # 验证目录创建
        self.assertTrue(self.archive_dir.exists())
        
        # 验证组件初始化
        self.assertIsNotNone(self.manager.image_scanner)
        self.assertIsNotNone(self.manager.yolo_manager)
        self.assertIsInstance(self.manager.archive_records, dict)
        
    def test_get_annotated_holes(self):
        """测试获取有标注的孔位"""
        annotated_holes = self.manager.get_annotated_holes()
        
        # 应该找到所有有标注的孔位
        self.assertGreater(len(annotated_holes), 0)
        self.assertIn("H00001", annotated_holes)
        self.assertIn("H00002", annotated_holes)
        self.assertIn("H00003", annotated_holes)
        
    def test_get_hole_annotation_summary(self):
        """测试获取孔位标注摘要"""
        summary = self.manager.get_hole_annotation_summary("H00001")
        
        # 验证摘要结构
        self.assertIn('hole_id', summary)
        self.assertIn('total_images', summary)
        self.assertIn('annotated_images', summary)
        self.assertIn('total_annotations', summary)
        self.assertIn('annotations_by_class', summary)
        
        # 验证数值
        self.assertEqual(summary['hole_id'], "H00001")
        self.assertEqual(summary['total_images'], 3)
        self.assertEqual(summary['annotated_images'], 2)  # 前两张图像有标注
        self.assertGreater(summary['total_annotations'], 0)
        
    def test_archive_hole(self):
        """测试归档孔位"""
        # 归档一个孔位
        success = self.manager.archive_hole("H00001", "测试归档")
        self.assertTrue(success)
        
        # 验证归档记录已创建
        self.assertIn("H00001", self.manager.archive_records)
        
        record = self.manager.archive_records["H00001"]
        self.assertEqual(record.hole_id, "H00001")
        self.assertEqual(record.notes, "测试归档")
        self.assertGreater(record.total_annotations, 0)
        
        # 验证归档文件已创建
        archive_hole_path = Path(record.archive_path)
        self.assertTrue(archive_hole_path.exists())
        
        # 验证元数据文件
        metadata_file = archive_hole_path / "archive_metadata.json"
        self.assertTrue(metadata_file.exists())
        
        # 尝试归档不存在的孔位
        success = self.manager.archive_hole("H99999", "不存在的孔位")
        self.assertFalse(success)
        
    def test_get_archived_holes(self):
        """测试获取已归档的孔位"""
        # 初始应该没有归档
        archived_holes = self.manager.get_archived_holes()
        initial_count = len(archived_holes)
        
        # 归档一个孔位
        self.manager.archive_hole("H00001")
        
        # 验证归档列表更新
        archived_holes = self.manager.get_archived_holes()
        self.assertEqual(len(archived_holes), initial_count + 1)
        self.assertIn("H00001", archived_holes)
        
    def test_get_archive_record(self):
        """测试获取归档记录"""
        # 获取不存在的记录
        record = self.manager.get_archive_record("H99999")
        self.assertIsNone(record)
        
        # 归档后获取记录
        self.manager.archive_hole("H00002", "测试记录")
        
        record = self.manager.get_archive_record("H00002")
        self.assertIsNotNone(record)
        self.assertEqual(record.hole_id, "H00002")
        self.assertEqual(record.notes, "测试记录")
        
    def test_load_archived_hole(self):
        """测试从归档加载孔位"""
        # 先归档一个孔位
        self.manager.archive_hole("H00001")
        
        # 删除原始数据
        original_path = self.data_dir / "H00001"
        if original_path.exists():
            shutil.rmtree(original_path)
            
        # 从归档加载
        success = self.manager.load_archived_hole("H00001")
        self.assertTrue(success)
        
        # 验证数据已恢复
        restored_path = self.data_dir / "H00001" / "BISDM" / "result"
        self.assertTrue(restored_path.exists())
        
        # 验证文件已恢复
        image_files = list(restored_path.glob("*.jpg"))
        annotation_files = list(restored_path.glob("*.txt"))
        
        self.assertGreater(len(image_files), 0)
        self.assertGreater(len(annotation_files), 0)
        
        # 尝试加载不存在的归档
        success = self.manager.load_archived_hole("H99999")
        self.assertFalse(success)
        
    def test_remove_archive(self):
        """测试删除归档"""
        # 先归档一个孔位
        self.manager.archive_hole("H00003")
        
        # 验证归档存在
        self.assertIn("H00003", self.manager.archive_records)
        
        # 删除归档
        success = self.manager.remove_archive("H00003")
        self.assertTrue(success)
        
        # 验证归档已删除
        self.assertNotIn("H00003", self.manager.archive_records)
        
        # 尝试删除不存在的归档
        success = self.manager.remove_archive("H99999")
        self.assertFalse(success)
        
    def test_save_and_load_archive_index(self):
        """测试保存和加载归档索引"""
        # 归档一些孔位
        self.manager.archive_hole("H00001", "索引测试1")
        self.manager.archive_hole("H00002", "索引测试2")
        
        # 保存索引
        success = self.manager.save_archive_index()
        self.assertTrue(success)
        self.assertTrue(self.manager.archive_index_file.exists())
        
        # 创建新的管理器实例加载索引
        new_manager = ArchiveManager(str(self.data_dir), str(self.archive_dir))
        
        # 验证索引已加载
        self.assertEqual(len(new_manager.archive_records), 2)
        self.assertIn("H00001", new_manager.archive_records)
        self.assertIn("H00002", new_manager.archive_records)
        
        # 验证记录内容
        record1 = new_manager.get_archive_record("H00001")
        record2 = new_manager.get_archive_record("H00002")
        
        self.assertEqual(record1.notes, "索引测试1")
        self.assertEqual(record2.notes, "索引测试2")
        
    def test_get_archive_statistics(self):
        """测试获取归档统计"""
        # 归档一些孔位
        self.manager.archive_hole("H00001")
        self.manager.archive_hole("H00002")
        
        # 获取统计信息
        stats = self.manager.get_archive_statistics()
        
        # 验证统计结构
        self.assertIn('total_archived_holes', stats)
        self.assertIn('total_archived_images', stats)
        self.assertIn('total_archived_annotations', stats)
        self.assertIn('archive_size_mb', stats)
        self.assertIn('annotations_by_class', stats)
        self.assertIn('recent_archives', stats)
        
        # 验证数值
        self.assertEqual(stats['total_archived_holes'], 2)
        self.assertGreater(stats['total_archived_images'], 0)
        self.assertGreater(stats['total_archived_annotations'], 0)
        self.assertGreaterEqual(stats['archive_size_mb'], 0)
        
    def test_export_archive_report(self):
        """测试导出归档报告"""
        # 归档一个孔位
        self.manager.archive_hole("H00001", "报告测试")
        
        # 导出报告
        report_file = self.temp_dir / "archive_report.json"
        success = self.manager.export_archive_report(str(report_file))
        
        self.assertTrue(success)
        self.assertTrue(report_file.exists())
        
        # 验证报告内容
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
            
        self.assertIn('generated_at', report)
        self.assertIn('statistics', report)
        self.assertIn('archive_records', report)
        
        # 验证报告数据
        self.assertEqual(len(report['archive_records']), 1)
        self.assertEqual(report['archive_records'][0]['hole_id'], "H00001")


class TestArchiveManagerIntegration(unittest.TestCase):
    """归档管理器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "Data"
        self.archive_dir = Path(self.temp_dir) / "Archive"
        
        # 创建简单的测试数据
        self.create_simple_test_data()
        
        self.manager = ArchiveManager(str(self.data_dir), str(self.archive_dir))
        
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def create_simple_test_data(self):
        """创建简单的测试数据"""
        hole_dir = self.data_dir / "H00001" / "BISDM" / "result"
        hole_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建图像和标注
        image_file = hole_dir / "test.jpg"
        image_file.write_bytes(b"test image")
        
        annotation_file = hole_dir / "test.txt"
        annotations = [DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)]
        YOLOFileManager.save_annotations(annotations, str(annotation_file))
        
    def test_complete_archive_workflow(self):
        """测试完整的归档工作流"""
        # 1. 检查有标注的孔位
        annotated_holes = self.manager.get_annotated_holes()
        self.assertIn("H00001", annotated_holes)
        
        # 2. 获取标注摘要
        summary = self.manager.get_hole_annotation_summary("H00001")
        self.assertEqual(summary['total_images'], 1)
        self.assertEqual(summary['annotated_images'], 1)
        self.assertGreater(summary['total_annotations'], 0)
        
        # 3. 归档孔位
        success = self.manager.archive_hole("H00001", "完整工作流测试")
        self.assertTrue(success)
        
        # 4. 验证归档
        archived_holes = self.manager.get_archived_holes()
        self.assertIn("H00001", archived_holes)
        
        # 5. 获取归档记录
        record = self.manager.get_archive_record("H00001")
        self.assertIsNotNone(record)
        self.assertEqual(record.notes, "完整工作流测试")
        
        # 6. 删除原始数据
        original_path = self.data_dir / "H00001"
        shutil.rmtree(original_path)
        
        # 7. 从归档恢复
        success = self.manager.load_archived_hole("H00001")
        self.assertTrue(success)
        
        # 8. 验证恢复的数据
        restored_image = self.data_dir / "H00001" / "BISDM" / "result" / "test.jpg"
        restored_annotation = self.data_dir / "H00001" / "BISDM" / "result" / "test.txt"
        
        self.assertTrue(restored_image.exists())
        self.assertTrue(restored_annotation.exists())
        
        # 9. 获取统计信息
        stats = self.manager.get_archive_statistics()
        self.assertEqual(stats['total_archived_holes'], 1)
        
        # 10. 导出报告
        report_file = self.temp_dir / "workflow_report.json"
        success = self.manager.export_archive_report(str(report_file))
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
