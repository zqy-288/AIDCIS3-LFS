#!/usr/bin/env python3
"""
配置类兼容性测试
确保模拟配置类与真实dataclass版本完全兼容
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

def test_configuration_compatibility():
    """测试配置类兼容性"""
    print("⚙️ 测试配置类兼容性...")
    
    # 尝试导入真实版本
    try:
        from assets.old.report_models import ReportConfiguration as RealConfig, ReportType as RealType, ReportFormat as RealFormat
        print("✅ 成功导入真实配置类")
        use_real = True
    except ImportError:
        print("⚠️ 无法导入真实配置类，将测试模拟版本")
        use_real = False
    
    # 导入模拟版本
    from report_generation_page import ReportConfiguration as MockConfig, ReportType as MockType, ReportFormat as MockFormat
    print("✅ 成功导入模拟配置类")
    
    # 测试模拟版本的各种初始化方式
    success_count = 0
    total_count = 0
    
    # 测试1：默认参数初始化
    total_count += 1
    try:
        config = MockConfig()
        assert hasattr(config, 'report_type')
        assert hasattr(config, 'report_format')
        assert config.report_type == MockType.COMPREHENSIVE
        assert config.report_format == MockFormat.PDF
        print("✅ 默认参数初始化成功")
        success_count += 1
    except Exception as e:
        print(f"❌ 默认参数初始化失败: {e}")
    
    # 测试2：关键字参数初始化
    total_count += 1
    try:
        config = MockConfig(report_type=MockType.QUALITY_ANALYSIS, report_format=MockFormat.HTML)
        assert config.report_type == MockType.QUALITY_ANALYSIS
        assert config.report_format == MockFormat.HTML
        print("✅ 关键字参数初始化成功")
        success_count += 1
    except Exception as e:
        print(f"❌ 关键字参数初始化失败: {e}")
    
    # 测试3：位置参数初始化
    total_count += 1
    try:
        config = MockConfig(MockType.DEFECT_ANALYSIS, MockFormat.EXCEL)
        assert config.report_type == MockType.DEFECT_ANALYSIS
        assert config.report_format == MockFormat.EXCEL
        print("✅ 位置参数初始化成功")
        success_count += 1
    except Exception as e:
        print(f"❌ 位置参数初始化失败: {e}")
    
    # 测试4：混合参数初始化
    total_count += 1
    try:
        config = MockConfig(
            MockType.COMPREHENSIVE, 
            MockFormat.PDF,
            include_workpiece_info=False,
            include_charts=True,
            chart_dpi=600
        )
        assert config.report_type == MockType.COMPREHENSIVE
        assert config.report_format == MockFormat.PDF
        assert config.include_workpiece_info == False
        assert config.include_charts == True
        assert config.chart_dpi == 600
        print("✅ 混合参数初始化成功")
        success_count += 1
    except Exception as e:
        print(f"❌ 混合参数初始化失败: {e}")
    
    # 测试5：检查所有必要属性
    total_count += 1
    try:
        config = MockConfig()
        required_attrs = [
            'report_type', 'report_format', 'include_workpiece_info',
            'include_quality_summary', 'include_qualified_holes', 'include_unqualified_holes',
            'include_defect_analysis', 'include_manual_reviews', 'include_charts',
            'include_endoscope_images', 'chart_dpi', 'chart_format',
            'page_size', 'page_orientation'
        ]
        
        for attr in required_attrs:
            assert hasattr(config, attr), f"缺少属性: {attr}"
        
        print("✅ 所有必要属性存在")
        success_count += 1
    except Exception as e:
        print(f"❌ 属性检查失败: {e}")
    
    # 如果有真实版本，比较兼容性
    if use_real:
        total_count += 1
        try:
            real_config = RealConfig(RealType.COMPREHENSIVE, RealFormat.PDF)
            mock_config = MockConfig(MockType.COMPREHENSIVE, MockFormat.PDF)
            
            # 比较关键属性
            assert real_config.report_type.value == mock_config.report_type.value
            assert real_config.report_format.value == mock_config.report_format.value
            assert real_config.include_workpiece_info == mock_config.include_workpiece_info
            assert real_config.include_charts == mock_config.include_charts
            
            print("✅ 与真实版本兼容性良好")
            success_count += 1
        except Exception as e:
            print(f"❌ 与真实版本兼容性失败: {e}")
    
    print(f"\n📊 配置类测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

if __name__ == "__main__":
    print("🚀 配置类兼容性测试")
    print("=" * 40)
    
    success = test_configuration_compatibility()
    
    if success:
        print("\n🎉 配置类兼容性测试全部通过！")
        sys.exit(0)
    else:
        print("\n❌ 配置类兼容性测试失败")
        sys.exit(1)