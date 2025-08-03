# 定时器竞争条件分析 - 蓝色永远不变绿的真正原因

## 问题描述
蓝色的孔位永远保持蓝色，不会在9.5秒后变成绿色。

## 根本原因：定时器被重置

### 当前的定时器机制
1. **simulation_timer**: 每10秒触发一次，处理下一对孔位
2. **status_change_timer**: 单次触发，9.5秒后将蓝色变为最终颜色

### 问题场景
```
理想情况：
0s: 第1对变蓝 → 设置9.5s定时器
9.5s: 第1对变绿（定时器触发）
10s: 第2对变蓝 → 设置新的9.5s定时器
19.5s: 第2对变绿

实际可能发生的情况：
0s: 第1对变蓝 → 设置9.5s定时器
8s: 某些操作导致提前处理下一对
8s: 第2对变蓝 → 重新设置9.5s定时器（覆盖了之前的！）
9.5s: 原定时器应该触发，但已被覆盖，第1对永远保持蓝色
17.5s: 新定时器触发，只有第2对变绿
```

## 代码证据

在 `_process_next_pair()` 中：
```python
# 启动状态变化定时器（9.5秒后变为最终状态）
self.status_change_timer.start(self.status_change_time)
```

**每次 `start()` 都会取消之前的定时器！**

## 验证方法

1. 检查日志中是否有：
   - "开始配对检测" 的间隔小于10秒
   - "开始更新检测单元的最终状态" 的数量少于 "开始配对检测"

2. 可能的触发条件：
   - 暂停/恢复操作
   - UI事件处理延迟
   - 系统负载导致的定时器不准确

## 解决方案

### 方案1：为每个检测单元使用独立的定时器
```python
def _start_pair_detection(self, hole_pair: HolePair):
    # ... 设置蓝色 ...
    
    # 为这个特定的配对创建独立定时器
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(lambda: self._finalize_specific_pair(hole_pair))
    timer.start(9500)
    
    # 保存定时器引用，防止被垃圾回收
    self._active_timers[hole_pair] = timer
```

### 方案2：使用队列管理待处理的状态变化
```python
def _start_pair_detection(self, hole_pair: HolePair):
    # ... 设置蓝色 ...
    
    # 记录应该变色的时间
    change_time = QDateTime.currentDateTime().addMSecs(9500)
    self._pending_changes.append((hole_pair, change_time))
    
    # 使用单个定时器定期检查
    if not self._check_timer.isActive():
        self._check_timer.start(100)  # 每100ms检查一次
```

### 方案3：确保定时器不会被覆盖（最简单）
```python
def _process_next_pair(self):
    # 如果状态变化定时器还在运行，等待它完成
    if self.status_change_timer.isActive():
        self.logger.warning("⚠️ 上一个状态变化定时器还在运行，跳过本次处理")
        return
    
    # ... 继续正常处理 ...
```

## 推荐修复

使用方案1（独立定时器）是最可靠的，因为：
1. 每个检测单元的状态变化是独立的
2. 不会相互干扰
3. 即使有延迟也能正确处理