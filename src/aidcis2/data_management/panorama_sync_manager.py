"""
全景图同步管理器
基于数据库轮询的全景图状态更新机制
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QTimer, QObject, Signal
from aidcis2.models.hole_data import HoleStatus


class PanoramaSyncManager(QObject):
    """全景图同步管理器"""
    
    # 定义信号
    status_updates_available = Signal(list)  # 有新的状态更新
    sync_completed = Signal(int)             # 同步完成，参数为更新数量
    sync_error = Signal(str)                 # 同步错误
    
    def __init__(self, db_manager, panorama_widget=None):
        super().__init__()
        self.db_manager = db_manager
        self.panorama_widget = panorama_widget
        
        # 同步配置
        self.sync_interval = 1000  # 1秒轮询间隔
        self.batch_size = 50       # 每次处理的最大更新数量
        self.auto_sync_enabled = True
        
        # 定时器
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_updates)
        
        # 状态跟踪
        self.last_sync_time = None
        self.total_synced = 0
        self.sync_errors = 0
        
        # 状态映射（数据库状态字符串 -> HoleStatus枚举）
        self.status_mapping = {
            'pending': HoleStatus.PENDING,
            'qualified': HoleStatus.QUALIFIED,
            'defective': HoleStatus.DEFECTIVE,
            'blind': HoleStatus.BLIND,
            'tie_rod': HoleStatus.TIE_ROD,
            'processing': HoleStatus.PROCESSING
        }
        
        print("🔄 [PanoramaSyncManager] 初始化完成")
    
    def start_sync(self, interval_ms: int = None):
        """开始自动同步"""
        if interval_ms:
            self.sync_interval = interval_ms
            
        self.auto_sync_enabled = True
        self.sync_timer.start(self.sync_interval)
        print(f"▶️ [PanoramaSyncManager] 开始自动同步，间隔: {self.sync_interval}ms")
    
    def stop_sync(self):
        """停止自动同步"""
        self.auto_sync_enabled = False
        self.sync_timer.stop()
        print("⏹️ [PanoramaSyncManager] 停止自动同步")
    
    def sync_updates(self):
        """执行同步更新"""
        try:
            # 获取待同步的状态更新
            pending_updates = self.db_manager.get_pending_status_updates(limit=self.batch_size)
            
            if not pending_updates:
                return  # 没有待更新的数据
            
            print(f"🔄 [PanoramaSyncManager] 发现 {len(pending_updates)} 个待同步更新")
            
            # 发送信号通知有新的更新
            self.status_updates_available.emit(pending_updates)
            
            # 如果有全景图组件，直接更新
            if self.panorama_widget:
                success_count = self._update_panorama_widget(pending_updates)
                
                if success_count > 0:
                    # 标记为已同步
                    update_ids = [update['id'] for update in pending_updates[:success_count]]
                    if self.db_manager.mark_status_updates_synced(update_ids):
                        self.total_synced += success_count
                        self.last_sync_time = datetime.now()
                        self.sync_completed.emit(success_count)
                        print(f"✅ [PanoramaSyncManager] 成功同步 {success_count} 个更新")
                    else:
                        self.sync_errors += 1
                        self.sync_error.emit("标记同步状态失败")
            
        except Exception as e:
            self.sync_errors += 1
            error_msg = f"同步过程发生错误: {e}"
            print(f"❌ [PanoramaSyncManager] {error_msg}")
            self.sync_error.emit(error_msg)
    
    def _update_panorama_widget(self, updates: List[Dict]) -> int:
        """更新全景图组件"""
        if not self.panorama_widget:
            return 0
        
        success_count = 0
        
        try:
            # 批量更新状态
            status_updates = {}
            for update in updates:
                hole_id = update['hole_id']
                new_status_str = update['new_status']
                
                # 转换状态字符串为枚举
                if new_status_str in self.status_mapping:
                    new_status = self.status_mapping[new_status_str]
                    status_updates[hole_id] = new_status
                    success_count += 1
                else:
                    print(f"⚠️ [PanoramaSyncManager] 未知状态: {new_status_str}")
            
            # 调用全景图批量更新方法
            if hasattr(self.panorama_widget, 'batch_update_hole_status'):
                self.panorama_widget.batch_update_hole_status(status_updates)
            elif hasattr(self.panorama_widget, 'update_hole_status'):
                # 逐个更新
                for hole_id, status in status_updates.items():
                    self.panorama_widget.update_hole_status(hole_id, status)
            else:
                print("❌ [PanoramaSyncManager] 全景图组件缺少更新方法")
                return 0
                
        except Exception as e:
            print(f"❌ [PanoramaSyncManager] 更新全景图失败: {e}")
            return 0
        
        return success_count
    
    def force_sync(self):
        """强制立即同步"""
        print("⚡ [PanoramaSyncManager] 强制立即同步")
        self.sync_updates()
    
    def set_panorama_widget(self, widget):
        """设置全景图组件"""
        self.panorama_widget = widget
        print(f"🔗 [PanoramaSyncManager] 设置全景图组件: {type(widget)}")
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        db_stats = self.db_manager.get_status_update_stats()
        
        return {
            'auto_sync_enabled': self.auto_sync_enabled,
            'sync_interval': self.sync_interval,
            'last_sync_time': self.last_sync_time,
            'total_synced': self.total_synced,
            'sync_errors': self.sync_errors,
            'db_stats': db_stats
        }
    
    def print_sync_status(self):
        """打印同步状态（调试用）"""
        stats = self.get_sync_stats()
        db_stats = stats['db_stats']
        
        print("\n📊 [PanoramaSyncManager] 同步状态:")
        print(f"  自动同步: {'启用' if stats['auto_sync_enabled'] else '禁用'}")
        print(f"  同步间隔: {stats['sync_interval']}ms")
        print(f"  上次同步: {stats['last_sync_time']}")
        print(f"  总同步数: {stats['total_synced']}")
        print(f"  同步错误: {stats['sync_errors']}")
        
        if db_stats:
            print(f"  数据库统计:")
            print(f"    总更新数: {db_stats['total_updates']}")
            print(f"    待同步数: {db_stats['pending_updates']}")
            print(f"    已同步数: {db_stats['synced_updates']}")
            print(f"    同步率: {db_stats['sync_rate']:.1f}%")


class StatusUpdateBuffer:
    """状态更新缓冲区 - 用于批量处理状态更新"""
    
    def __init__(self, db_manager, buffer_size=100, flush_interval=5.0):
        self.db_manager = db_manager
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        self.buffer = []
        self.last_flush_time = time.time()
        
    def add_update(self, hole_id: str, new_status: str, update_source: str = "detection", 
                   operator_id: str = None, batch_id: str = None):
        """添加状态更新到缓冲区"""
        update = {
            'hole_id': hole_id,
            'new_status': new_status,
            'update_source': update_source,
            'operator_id': operator_id,
            'batch_id': batch_id,
            'timestamp': datetime.now()
        }
        
        self.buffer.append(update)
        
        # 检查是否需要刷新
        if (len(self.buffer) >= self.buffer_size or 
            time.time() - self.last_flush_time >= self.flush_interval):
            self.flush()
    
    def flush(self):
        """刷新缓冲区，将所有更新写入数据库"""
        if not self.buffer:
            return
        
        print(f"💾 [StatusUpdateBuffer] 刷新缓冲区，{len(self.buffer)} 个更新")
        
        # 批量处理更新
        for update in self.buffer:
            self.db_manager.update_hole_status(
                hole_id=update['hole_id'],
                new_status=update['new_status'],
                update_source=update['update_source'],
                operator_id=update['operator_id'],
                batch_id=update['batch_id']
            )
        
        # 清空缓冲区
        self.buffer.clear()
        self.last_flush_time = time.time()
        
        print(f"✅ [StatusUpdateBuffer] 缓冲区已刷新")
    
    def __del__(self):
        """析构时确保数据被保存"""
        self.flush()