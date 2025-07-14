"""
批量数据管理器
用于处理10个孔位的批量数据收集、存储和分发
"""

import json
import time
import random
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from aidcis2.models.hole_data import HoleData, HoleStatus


@dataclass
class BatchHoleData:
    """批量处理的孔位数据结构"""
    hole_id: str
    center_x: float
    center_y: float
    radius: float
    row: int
    column: int
    status: str  # HoleStatus的字符串表示
    sector: str  # SectorQuadrant的字符串表示
    timestamp: float
    
    @classmethod
    def from_hole_data(cls, hole: HoleData, status: HoleStatus, sector: str) -> 'BatchHoleData':
        """从HoleData创建BatchHoleData"""
        return cls(
            hole_id=hole.hole_id,
            center_x=hole.center_x,
            center_y=hole.center_y,
            radius=hole.radius,
            row=hole.row or 0,
            column=hole.column or 0,
            status=status.value if status else "unknown",
            sector=sector,
            timestamp=time.time()
        )


@dataclass
class DataBatch:
    """批量数据结构"""
    batch_id: str
    timestamp: str
    total_holes: int
    holes: List[BatchHoleData]
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DataBatch':
        """从JSON字符串创建"""
        data = json.loads(json_str)
        holes = [BatchHoleData(**hole_data) for hole_data in data['holes']]
        return cls(
            batch_id=data['batch_id'],
            timestamp=data['timestamp'],
            total_holes=data['total_holes'],
            holes=holes
        )


class BatchDataManager:
    """批量数据管理器"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path("src/data")
        elif isinstance(data_dir, str):
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        # 批量数据缓存
        self.current_batch: Optional[DataBatch] = None
        self.batch_size = 10
        self.batch_counter = 0
        
        # 全局状态分配计数器
        self.total_processed_holes = 0
        
        # 随机种子（可选）
        self.random_seed = None
        
        # 分发队列
        self.render_queue: List[BatchHoleData] = []
        self.current_render_index = 0
        
    def create_batch(self, holes: List[HoleData], sector: str) -> DataBatch:
        """创建批量数据"""
        self.batch_counter += 1
        batch_id = f"batch_{self.batch_counter:04d}_{int(time.time())}"
        
        # 模拟正确的状态分布：99.5%合格，0.4%不合格，0.1%其他
        # 使用随机分配但保持准确比例
        batch_holes = []
        batch_size_actual = len(holes[:self.batch_size])
        
        # 计算各状态的准确数量
        qualified_count = round(batch_size_actual * 0.995)  # 99.5%
        defective_count = round(batch_size_actual * 0.004)  # 0.4% 
        pending_count = batch_size_actual - qualified_count - defective_count  # 剩余为待检
        
        # 创建状态列表
        status_list = (
            [HoleStatus.QUALIFIED] * qualified_count +
            [HoleStatus.DEFECTIVE] * defective_count +
            [HoleStatus.PENDING] * pending_count
        )
        
        # 确保列表长度匹配
        while len(status_list) < batch_size_actual:
            status_list.append(HoleStatus.QUALIFIED)  # 补齐为合格状态
        while len(status_list) > batch_size_actual:
            status_list.pop()  # 移除多余状态
        
        # 随机打散状态分配（如果设置了种子则使用固定种子）
        if self.random_seed is not None:
            # 使用批次计数器作为种子的一部分，确保每批不同但可重现
            current_seed = self.random_seed + self.batch_counter
            random.seed(current_seed)
        
        random.shuffle(status_list)
        
        # 分配状态到孔位
        for i, hole in enumerate(holes[:self.batch_size]):
            status = status_list[i]
            batch_hole = BatchHoleData.from_hole_data(hole, status, sector)
            batch_holes.append(batch_hole)
        
        # 更新全局处理计数器
        self.total_processed_holes += len(batch_holes)
        
        # 调试信息：显示状态分配情况
        status_count = {"QUALIFIED": 0, "DEFECTIVE": 0, "PENDING": 0}
        for hole in batch_holes:
            status_count[hole.status] = status_count.get(hole.status, 0) + 1
        
        # 计算实际比例
        total = len(batch_holes)
        qualified_ratio = status_count.get('QUALIFIED', 0) / total * 100 if total > 0 else 0
        defective_ratio = status_count.get('DEFECTIVE', 0) / total * 100 if total > 0 else 0
        pending_ratio = status_count.get('PENDING', 0) / total * 100 if total > 0 else 0
        
        print(f"📊 [批量数据] 第{self.batch_counter}批随机分配: "
              f"合格={status_count.get('QUALIFIED', 0)}({qualified_ratio:.1f}%), "
              f"异常={status_count.get('DEFECTIVE', 0)}({defective_ratio:.1f}%), "
              f"待检={status_count.get('PENDING', 0)}({pending_ratio:.1f}%) "
              f"(目标: 99.5%/0.4%/0.1%)")
        
        batch = DataBatch(
            batch_id=batch_id,
            timestamp=datetime.now().isoformat(),
            total_holes=len(batch_holes),
            holes=batch_holes
        )
        
        return batch
    
    def save_batch(self, batch: DataBatch) -> Path:
        """保存批量数据到JSON文件（原子写入）"""
        file_path = self.data_dir / f"{batch.batch_id}.json"
        temp_path = file_path.with_suffix('.json.tmp')
        
        try:
            # 先写入临时文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(batch.to_json())
                f.flush()  # 确保数据写入磁盘
            
            # 原子操作：重命名临时文件为目标文件
            temp_path.replace(file_path)
            
            print(f"💾 [批量数据] 保存批量数据: {file_path}")
            return file_path
            
        except Exception as e:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            print(f"❌ [批量数据] 保存失败: {e}")
            raise
    
    def load_batch(self, batch_id: str) -> Optional[DataBatch]:
        """从JSON文件加载批量数据（带重试机制）"""
        file_path = self.data_dir / f"{batch_id}.json"
        if not file_path.exists():
            print(f"❌ [批量数据] 文件不存在: {file_path}")
            return None
        
        # 重试机制，最多尝试3次
        import time
        import json
        for attempt in range(3):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():  # 检查文件是否为空
                        raise ValueError("文件内容为空")
                    batch = DataBatch.from_json(content)
                print(f"📂 [批量数据] 加载批量数据: {batch_id}, {len(batch.holes)}个孔位")
                return batch
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < 2:  # 前两次尝试失败时等待重试
                    print(f"⚠️ [批量数据] 读取失败，第{attempt+1}次重试: {e}")
                    time.sleep(0.01)  # 等待10ms后重试
                    continue
                else:
                    print(f"❌ [批量数据] 最终加载失败: {e}")
                    return None
            except Exception as e:
                print(f"❌ [批量数据] 加载失败: {e}")
                return None
        
        return None
    
    def prepare_batch_for_rendering(self, batch: DataBatch):
        """准备批量数据用于渲染"""
        self.current_batch = batch
        self.render_queue = batch.holes.copy()
        self.current_render_index = 0
        print(f"🎬 [批量数据] 准备渲染队列: {len(self.render_queue)}个孔位")
    
    def get_next_render_item(self) -> Optional[BatchHoleData]:
        """获取下一个要渲染的孔位数据"""
        if not self.render_queue or self.current_render_index >= len(self.render_queue):
            return None
        
        item = self.render_queue[self.current_render_index]
        self.current_render_index += 1
        
        print(f"🎯 [批量数据] 获取渲染项 {self.current_render_index}/{len(self.render_queue)}: {item.hole_id}")
        return item
    
    def is_batch_complete(self) -> bool:
        """检查当前批次是否渲染完成"""
        return self.current_render_index >= len(self.render_queue)
    
    def get_rendering_progress(self) -> float:
        """获取当前渲染进度(0.0-1.0)"""
        if not self.render_queue:
            return 1.0
        return self.current_render_index / len(self.render_queue)
    
    def reset_rendering(self):
        """重置渲染状态"""
        self.current_render_index = 0
        print(f"🔄 [批量数据] 重置渲染状态")
    
    def reset_simulation(self):
        """重置模拟状态（新模拟开始时调用）"""
        self.total_processed_holes = 0
        self.batch_counter = 0
        self.current_render_index = 0
        self.render_queue.clear()
        print(f"🔄 [批量数据] 重置模拟状态，全局计数器归零")
    
    def set_random_seed(self, seed: Optional[int] = None):
        """设置随机种子（None表示使用真随机）"""
        self.random_seed = seed
        if seed is not None:
            print(f"🎲 [批量数据] 设置随机种子: {seed}")
        else:
            print(f"🎲 [批量数据] 使用真随机模式")
    
    def generate_simulation_batch(self, holes: List[HoleData], sector: str) -> DataBatch:
        """生成模拟数据批次（包含1000ms写入的模拟）"""
        print(f"⚡ [批量数据] 开始生成模拟批次: {len(holes)}个孔位, 扇形: {sector}")
        
        # 模拟1000ms的数据收集过程
        batch = self.create_batch(holes, sector)
        
        # 保存到JSON文件
        self.save_batch(batch)
        
        # 准备渲染
        self.prepare_batch_for_rendering(batch)
        
        print(f"✅ [批量数据] 模拟批次生成完成: {batch.batch_id}")
        return batch