
🎯 零容忍测试报告
==================

总测试数: 5
通过: 2 ✅
失败: 3 ❌
修复迭代: 3

详细结果:
---------
✅ 服务层集成测试
   services_initialized: 4
   service_status: {'_file_service': True, '_search_service': True, '_status_service': True, '_detection_service': True}
✅ 性能基准测试
   initial_memory_mb: 180.859375
   peak_memory_mb: 181.015625
   final_memory_mb: 181.015625
   memory_growth_mb: 0.15625
   memory_cleanup_mb: 0.0
❌ 主窗口创建测试: 主窗口导入时间过长: 8.381s
❌ MVVM架构测试: 视图模型缺少属性: ['window_title', 'total_holes_count']
❌ DXF解析器测试: DXF解析没有提取到孔位
