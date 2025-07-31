# 扇形分配逻辑重构计划

## 目标
将扇形分配逻辑从 `core_business` 移到 `pages` 目录下，使架构更清晰。

## 已完成
1. ✅ 创建了 `/src/pages/main_detection_p1/components/sector_assignment_manager.py`
   - 包含正确的Qt坐标系扇形分配逻辑
   - 提供与原 UnifiedCoordinateManager 相同的接口

2. ✅ 更新了 `panorama_sector_coordinator.py`
   - 使用新的 SectorAssignmentManager
   - 移除了内部的扇形分配逻辑

3. ✅ 更新了 `dxf_loader_service.py`
   - 移除了对 UnifiedCoordinateManager 的无用引用

## 需要更新的文件

### 1. 核心依赖文件
- [ ] `/src/core_business/graphics/unified_sector_adapter.py`
  - 这是一个适配器，严重依赖 UnifiedCoordinateManager
  - 需要评估是否还在使用，或者重写使用新的 SectorAssignmentManager

### 2. 可能受影响的文件
- [ ] `/src/core/shared_data_manager.py` 
  - 可能使用了 unified_adapter
  - 需要检查并更新引用

- [ ] 主窗口相关文件
  - 需要确保使用新的扇形分配逻辑

### 3. 需要删除的冗余文件
- [ ] `/src/core_business/coordinate_system.py` - 旧的坐标系统管理
- [ ] `/src/business/` 整个目录 - 与 core_business 重复

## 重构步骤

### 第一阶段：评估影响范围
1. 搜索所有引用 UnifiedCoordinateManager 的文件
2. 确定哪些是真正需要的，哪些可以直接删除
3. 评估 unified_sector_adapter 的使用情况

### 第二阶段：逐步替换
1. 对于简单引用，直接替换为新的 SectorAssignmentManager
2. 对于复杂依赖，可能需要创建适配层
3. 确保所有测试通过

### 第三阶段：清理
1. 删除不再使用的旧文件
2. 更新导入路径
3. 运行完整测试确保功能正常

## 注意事项

1. **坐标系问题**：新的实现已经修复了Qt坐标系Y轴翻转的问题
2. **向后兼容**：某些组件可能依赖旧的接口，需要保持兼容
3. **性能考虑**：新实现使用了相同的算法，性能应该相当

## 风险评估

- **中等风险**：unified_sector_adapter 被多个组件使用，需要仔细处理
- **低风险**：扇形分配逻辑本身相对独立，易于替换
- **需要测试**：确保扇形点击、显示、统计等功能正常工作