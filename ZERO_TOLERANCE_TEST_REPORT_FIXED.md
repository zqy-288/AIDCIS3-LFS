
🎯 零容忍测试报告 (修复版)
=========================

总测试数: 5
通过: 5 ✅
失败: 0 ❌
修复迭代: 0

详细结果:
---------
✅ 主窗口创建测试 (优化版)
   import_time: 0.011828899383544922
   creation_time: 0.0003829002380371094
   component_status: {'components_loaded': True, 'main_view_model': True, 'main_business_controller': True, 'view_model_manager': True}
   window_size: (1200, 800)
✅ MVVM架构测试 (修复版)
   components_created: 3
   view_model_attrs: {'window_title': 'AIDCIS3-LFS 工业检测系统', 'current_file_path': None, 'total_holes_count': 0}
✅ DXF解析器测试 (含测试数据)
   parse_time: 0.008788824081420898
   test_file: /Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf
   file_size: 17683
   hole_count: 9
✅ 服务层集成测试
   available_products: ['东重管板', '测试管板', '标准管板']
   services_initialized: 4
   service_status: {'_file_service': True, '_search_service': True, '_status_service': True, '_detection_service': True}
✅ 性能基准测试
   initial_memory_mb: 130.3125
   peak_memory_mb: 130.375
   final_memory_mb: 130.375
   memory_growth_mb: 0.0625
   memory_cleanup_mb: 0.0
