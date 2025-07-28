"""
High-Performance Data Loader for Large Datasets
Implements streaming, chunking, and progressive loading for optimal performance
"""

import time
import threading
import multiprocessing as mp
from typing import Dict, Any, List, Optional, Callable, Iterator, Generator
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, Empty
from PySide6.QtCore import QObject, Signal, QTimer

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus


class LoadingStrategy(Enum):
    """Data loading strategy options"""
    SEQUENTIAL = "sequential"          # Load data sequentially
    CHUNKED = "chunked"               # Load data in chunks
    STREAMING = "streaming"           # Stream data progressively
    PARALLEL = "parallel"             # Parallel loading with threads
    MULTIPROCESS = "multiprocess"     # Multiprocess loading for CPU-intensive tasks


@dataclass
class LoadingProgress:
    """Progress information for data loading"""
    current_items: int
    total_items: int
    current_chunk: int
    total_chunks: int
    processing_rate: float  # items per second
    estimated_time_remaining: float  # seconds
    memory_usage_mb: float
    errors_count: int


@dataclass
class ChunkInfo:
    """Information about a data chunk"""
    chunk_id: int
    start_index: int
    end_index: int
    size: int
    data: Optional[List[Any]] = None
    processing_time: float = 0.0
    memory_size_mb: float = 0.0


class DataStreamProcessor:
    """
    Processes data streams with configurable batch sizes and processing functions
    """
    
    def __init__(self, 
                 batch_size: int = 1000,
                 max_memory_mb: float = 500.0,
                 processing_threads: int = 4):
        self.batch_size = batch_size
        self.max_memory_mb = max_memory_mb
        self.processing_threads = processing_threads
        self.executor = ThreadPoolExecutor(max_workers=processing_threads)
        
    def process_stream(self, 
                      data_iterator: Iterator[Any],
                      processor_func: Callable[[List[Any]], List[Any]],
                      progress_callback: Optional[Callable[[LoadingProgress], None]] = None) -> Generator[List[Any], None, None]:
        """
        Process data stream in batches
        
        Args:
            data_iterator: Iterator providing data items
            processor_func: Function to process each batch
            progress_callback: Optional callback for progress updates
            
        Yields:
            Processed batches of data
        """
        batch = []
        total_processed = 0
        start_time = time.time()
        
        try:
            for item in data_iterator:
                batch.append(item)
                
                if len(batch) >= self.batch_size:
                    # Process batch
                    processed_batch = processor_func(batch)
                    total_processed += len(batch)
                    
                    # Update progress
                    if progress_callback:
                        current_time = time.time()
                        elapsed = current_time - start_time
                        rate = total_processed / elapsed if elapsed > 0 else 0
                        
                        progress = LoadingProgress(
                            current_items=total_processed,
                            total_items=-1,  # Unknown for streaming
                            current_chunk=total_processed // self.batch_size,
                            total_chunks=-1,
                            processing_rate=rate,
                            estimated_time_remaining=-1,
                            memory_usage_mb=self._estimate_memory_usage(batch),
                            errors_count=0
                        )
                        progress_callback(progress)
                    
                    yield processed_batch
                    batch = []
                    
            # Process remaining items
            if batch:
                processed_batch = processor_func(batch)
                yield processed_batch
                
        finally:
            self.executor.shutdown(wait=False)
            
    def _estimate_memory_usage(self, data: List[Any]) -> float:
        """Estimate memory usage of data in MB"""
        try:
            import sys
            total_size = sum(sys.getsizeof(item) for item in data)
            return total_size / 1024 / 1024
        except:
            return 0.0


class OptimizedDataLoader(QObject):
    """
    High-performance data loader with multiple strategies and optimization
    """
    
    # Signals for loading progress and completion
    loading_started = Signal(str, int)  # strategy, total_items
    loading_progress = Signal(object)   # LoadingProgress
    chunk_loaded = Signal(object)       # ChunkInfo
    loading_completed = Signal(int, float)  # total_items, total_time
    loading_failed = Signal(str)        # error_message
    
    def __init__(self):
        super().__init__()
        
        # Configuration
        self.default_chunk_size = 1000
        self.max_memory_threshold_mb = 1000.0
        self.max_worker_threads = min(8, mp.cpu_count())
        
        # State tracking
        self.loading_active = False
        self.current_strategy = LoadingStrategy.CHUNKED
        self.loaded_chunks: Dict[int, ChunkInfo] = {}
        
        # Performance tracking
        self.loading_stats = {
            "total_loads": 0,
            "average_load_time": 0.0,
            "peak_memory_usage": 0.0,
            "total_items_loaded": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Cache for frequently accessed data
        self.data_cache: Dict[str, Any] = {}
        self.cache_access_times: Dict[str, float] = {}
        self.max_cache_size = 100
        
        # Progress timer for UI updates
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._emit_progress_update)
        
    def load_hole_collection_optimized(self, 
                                     data_source: Any,
                                     strategy: LoadingStrategy = LoadingStrategy.CHUNKED,
                                     chunk_size: Optional[int] = None,
                                     progress_callback: Optional[Callable] = None) -> HoleCollection:
        """
        Load hole collection with optimization strategy
        
        Args:
            data_source: Source of hole data (file path, raw data, etc.)
            strategy: Loading strategy to use
            chunk_size: Size of chunks for chunked loading
            progress_callback: Optional progress callback
            
        Returns:
            Optimized HoleCollection
        """
        if self.loading_active:
            raise RuntimeError("Loading already in progress")
            
        self.loading_active = True
        self.current_strategy = strategy
        chunk_size = chunk_size or self.default_chunk_size
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(data_source, strategy)
            if cache_key in self.data_cache:
                self.loading_stats["cache_hits"] += 1
                cached_result = self.data_cache[cache_key]
                self.cache_access_times[cache_key] = time.time()
                self.loading_completed.emit(len(cached_result.holes), 0.0)
                return cached_result
                
            self.loading_stats["cache_misses"] += 1
            
            # Determine total items for progress tracking
            total_items = self._estimate_total_items(data_source)
            self.loading_started.emit(strategy.value, total_items)
            
            # Start progress timer
            self.progress_timer.start(100)  # Update every 100ms
            
            # Load data based on strategy
            if strategy == LoadingStrategy.SEQUENTIAL:
                result = self._load_sequential(data_source, progress_callback)
            elif strategy == LoadingStrategy.CHUNKED:
                result = self._load_chunked(data_source, chunk_size, progress_callback)
            elif strategy == LoadingStrategy.STREAMING:
                result = self._load_streaming(data_source, progress_callback)
            elif strategy == LoadingStrategy.PARALLEL:
                result = self._load_parallel(data_source, chunk_size, progress_callback)
            elif strategy == LoadingStrategy.MULTIPROCESS:
                result = self._load_multiprocess(data_source, chunk_size, progress_callback)
            else:
                raise ValueError(f"Unsupported loading strategy: {strategy}")
                
            # Cache result if it's not too large
            result_size_mb = self._estimate_collection_size(result)
            if result_size_mb < self.max_memory_threshold_mb / 10:  # Cache if < 10% of memory threshold
                self._add_to_cache(cache_key, result)
                
            # Update statistics
            load_time = time.time() - start_time
            self._update_loading_stats(len(result.holes), load_time, result_size_mb)
            
            self.loading_completed.emit(len(result.holes), load_time)
            return result
            
        except Exception as e:
            error_msg = f"Loading failed with {strategy.value} strategy: {str(e)}"
            self.loading_failed.emit(error_msg)
            raise
            
        finally:
            self.loading_active = False
            self.progress_timer.stop()
            
    def _load_sequential(self, data_source: Any, progress_callback: Optional[Callable]) -> HoleCollection:
        """Load data sequentially"""
        holes = {}
        raw_data = self._extract_raw_data(data_source)
        
        total_items = len(raw_data)
        
        for i, item in enumerate(raw_data):
            hole = self._convert_to_hole_data(item, i)
            holes[hole.hole_id] = hole
            
            # Progress update
            if progress_callback and i % 100 == 0:
                progress = self._create_progress_info(i + 1, total_items, 1, 1)
                progress_callback(progress)
                
        collection = HoleCollection()
        collection.holes = holes
        return collection
        
    def _load_chunked(self, data_source: Any, chunk_size: int, progress_callback: Optional[Callable]) -> HoleCollection:
        """Load data in chunks"""
        raw_data = self._extract_raw_data(data_source)
        total_items = len(raw_data)
        total_chunks = (total_items + chunk_size - 1) // chunk_size
        
        holes = {}
        current_items = 0
        
        for chunk_id in range(total_chunks):
            start_idx = chunk_id * chunk_size
            end_idx = min(start_idx + chunk_size, total_items)
            chunk_data = raw_data[start_idx:end_idx]
            
            chunk_start_time = time.time()
            
            # Process chunk
            for i, item in enumerate(chunk_data):
                global_idx = start_idx + i
                hole = self._convert_to_hole_data(item, global_idx)
                holes[hole.hole_id] = hole
                
            chunk_time = time.time() - chunk_start_time
            current_items += len(chunk_data)
            
            # Create chunk info
            chunk_info = ChunkInfo(
                chunk_id=chunk_id,
                start_index=start_idx,
                end_index=end_idx,
                size=len(chunk_data),
                processing_time=chunk_time,
                memory_size_mb=self._estimate_chunk_memory(chunk_data)
            )
            
            self.loaded_chunks[chunk_id] = chunk_info
            self.chunk_loaded.emit(chunk_info)
            
            # Progress update
            if progress_callback:
                progress = self._create_progress_info(current_items, total_items, chunk_id + 1, total_chunks)
                progress_callback(progress)
                
        collection = HoleCollection()
        collection.holes = holes
        return collection
        
    def _load_streaming(self, data_source: Any, progress_callback: Optional[Callable]) -> HoleCollection:
        """Load data using streaming approach"""
        holes = {}
        processor = DataStreamProcessor(batch_size=500, max_memory_mb=self.max_memory_threshold_mb)
        
        def hole_converter(batch: List[Any]) -> List[HoleData]:
            return [self._convert_to_hole_data(item, i) for i, item in enumerate(batch)]
            
        data_iterator = self._create_data_iterator(data_source)
        
        for processed_batch in processor.process_stream(data_iterator, hole_converter, progress_callback):
            for hole in processed_batch:
                holes[hole.hole_id] = hole
                
        collection = HoleCollection()
        collection.holes = holes
        return collection
        
    def _load_parallel(self, data_source: Any, chunk_size: int, progress_callback: Optional[Callable]) -> HoleCollection:
        """Load data using parallel processing"""
        raw_data = self._extract_raw_data(data_source)
        total_items = len(raw_data)
        total_chunks = (total_items + chunk_size - 1) // chunk_size
        
        holes = {}
        
        with ThreadPoolExecutor(max_workers=self.max_worker_threads) as executor:
            # Submit all chunks for processing
            futures = []
            for chunk_id in range(total_chunks):
                start_idx = chunk_id * chunk_size
                end_idx = min(start_idx + chunk_size, total_items)
                chunk_data = raw_data[start_idx:end_idx]
                
                future = executor.submit(self._process_chunk_parallel, chunk_data, start_idx)
                futures.append((chunk_id, future))
                
            # Collect results as they complete
            completed_chunks = 0
            for chunk_id, future in futures:
                try:
                    chunk_holes = future.result(timeout=60)  # 60 second timeout per chunk
                    holes.update(chunk_holes)
                    completed_chunks += 1
                    
                    # Progress update
                    if progress_callback:
                        current_items = min(completed_chunks * chunk_size, total_items)
                        progress = self._create_progress_info(current_items, total_items, completed_chunks, total_chunks)
                        progress_callback(progress)
                        
                except Exception as e:
                    print(f"Error processing chunk {chunk_id}: {e}")
                    
        collection = HoleCollection()
        collection.holes = holes
        return collection
        
    def _load_multiprocess(self, data_source: Any, chunk_size: int, progress_callback: Optional[Callable]) -> HoleCollection:
        """Load data using multiprocessing"""
        raw_data = self._extract_raw_data(data_source)
        total_items = len(raw_data)
        total_chunks = (total_items + chunk_size - 1) // chunk_size
        
        holes = {}
        
        with ProcessPoolExecutor(max_workers=min(self.max_worker_threads, 4)) as executor:  # Limit processes
            # Submit chunks for processing
            futures = []
            for chunk_id in range(total_chunks):
                start_idx = chunk_id * chunk_size
                end_idx = min(start_idx + chunk_size, total_items)
                chunk_data = raw_data[start_idx:end_idx]
                
                future = executor.submit(_process_chunk_multiprocess, chunk_data, start_idx)
                futures.append((chunk_id, future))
                
            # Collect results
            completed_chunks = 0
            for chunk_id, future in as_completed([f for _, f in futures]):
                try:
                    chunk_holes = future.result()
                    holes.update(chunk_holes)
                    completed_chunks += 1
                    
                    if progress_callback:
                        current_items = min(completed_chunks * chunk_size, total_items)
                        progress = self._create_progress_info(current_items, total_items, completed_chunks, total_chunks)
                        progress_callback(progress)
                        
                except Exception as e:
                    print(f"Error in multiprocess chunk: {e}")
                    
        collection = HoleCollection()
        collection.holes = holes
        return collection
        
    def _process_chunk_parallel(self, chunk_data: List[Any], start_idx: int) -> Dict[str, HoleData]:
        """Process a chunk of data in parallel"""
        holes = {}
        for i, item in enumerate(chunk_data):
            global_idx = start_idx + i
            hole = self._convert_to_hole_data(item, global_idx)
            holes[hole.hole_id] = hole
        return holes
        
    def _extract_raw_data(self, data_source: Any) -> List[Any]:
        """Extract raw data from various source types"""
        if isinstance(data_source, str):
            # File path
            return self._load_from_file(data_source)
        elif isinstance(data_source, list):
            # Already a list
            return data_source
        elif hasattr(data_source, 'holes'):
            # HoleCollection
            return list(data_source.holes.values())
        else:
            # Try to convert to list
            return list(data_source)
            
    def _load_from_file(self, file_path: str) -> List[Any]:
        """Load data from file (placeholder implementation)"""
        # This would use the actual DXF parser
        # For now, generate test data
        return [{"id": f"H{i:03d}", "x": i * 10, "y": 50, "radius": 5} for i in range(10000)]
        
    def _create_data_iterator(self, data_source: Any) -> Iterator[Any]:
        """Create an iterator for streaming data"""
        raw_data = self._extract_raw_data(data_source)
        return iter(raw_data)
        
    def _convert_to_hole_data(self, item: Any, index: int) -> HoleData:
        """Convert raw item to HoleData"""
        if isinstance(item, HoleData):
            return item
        elif isinstance(item, dict):
            return HoleData(
                hole_id=item.get("id", f"H{index:03d}"),
                center_x=float(item.get("x", index * 10)),
                center_y=float(item.get("y", 50)),
                radius=float(item.get("radius", 5)),
                status=HoleStatus.PENDING
            )
        else:
            return HoleData(
                hole_id=f"H{index:03d}",
                center_x=index * 10.0,
                center_y=50.0,
                radius=5.0,
                status=HoleStatus.PENDING
            )
            
    def _estimate_total_items(self, data_source: Any) -> int:
        """Estimate total number of items"""
        if isinstance(data_source, list):
            return len(data_source)
        elif hasattr(data_source, '__len__'):
            return len(data_source)
        else:
            return -1  # Unknown
            
    def _create_progress_info(self, current: int, total: int, current_chunk: int, total_chunks: int) -> LoadingProgress:
        """Create progress information"""
        rate = current / max(time.time() - self.loading_stats.get("start_time", time.time()), 0.001)
        eta = (total - current) / rate if rate > 0 and total > 0 else -1
        
        return LoadingProgress(
            current_items=current,
            total_items=total,
            current_chunk=current_chunk,
            total_chunks=total_chunks,
            processing_rate=rate,
            estimated_time_remaining=eta,
            memory_usage_mb=self._get_current_memory_usage(),
            errors_count=0
        )
        
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
            
    def _estimate_collection_size(self, collection: HoleCollection) -> float:
        """Estimate size of hole collection in MB"""
        try:
            import sys
            return sys.getsizeof(collection) / 1024 / 1024
        except:
            return 0.0
            
    def _estimate_chunk_memory(self, chunk_data: List[Any]) -> float:
        """Estimate memory usage of chunk data"""
        try:
            import sys
            return sum(sys.getsizeof(item) for item in chunk_data) / 1024 / 1024
        except:
            return 0.0
            
    def _generate_cache_key(self, data_source: Any, strategy: LoadingStrategy) -> str:
        """Generate cache key for data source and strategy"""
        source_hash = hash(str(data_source))
        return f"{strategy.value}_{source_hash}"
        
    def _add_to_cache(self, key: str, data: HoleCollection):
        """Add data to cache with LRU eviction"""
        if len(self.data_cache) >= self.max_cache_size:
            # Remove least recently used item
            lru_key = min(self.cache_access_times.keys(), key=self.cache_access_times.get)
            del self.data_cache[lru_key]
            del self.cache_access_times[lru_key]
            
        self.data_cache[key] = data
        self.cache_access_times[key] = time.time()
        
    def _update_loading_stats(self, items_loaded: int, load_time: float, memory_usage: float):
        """Update loading statistics"""
        self.loading_stats["total_loads"] += 1
        self.loading_stats["total_items_loaded"] += items_loaded
        
        # Update average load time
        total_loads = self.loading_stats["total_loads"]
        current_avg = self.loading_stats["average_load_time"]
        new_avg = (current_avg * (total_loads - 1) + load_time) / total_loads
        self.loading_stats["average_load_time"] = new_avg
        
        # Update peak memory usage
        if memory_usage > self.loading_stats["peak_memory_usage"]:
            self.loading_stats["peak_memory_usage"] = memory_usage
            
    def _emit_progress_update(self):
        """Emit progress update for UI"""
        if hasattr(self, '_current_progress'):
            self.loading_progress.emit(self._current_progress)
            
    def get_loading_statistics(self) -> Dict[str, Any]:
        """Get comprehensive loading statistics"""
        return {
            **self.loading_stats,
            "cache_size": len(self.data_cache),
            "loaded_chunks_count": len(self.loaded_chunks),
            "current_strategy": self.current_strategy.value if self.current_strategy else None,
            "loading_active": self.loading_active
        }
        
    def clear_cache(self):
        """Clear the data cache"""
        self.data_cache.clear()
        self.cache_access_times.clear()
        
    def optimize_loading_strategy(self, data_size_estimate: int) -> LoadingStrategy:
        """Recommend optimal loading strategy based on data size"""
        if data_size_estimate < 1000:
            return LoadingStrategy.SEQUENTIAL
        elif data_size_estimate < 10000:
            return LoadingStrategy.CHUNKED
        elif data_size_estimate < 100000:
            return LoadingStrategy.PARALLEL
        else:
            return LoadingStrategy.MULTIPROCESS


# Standalone function for multiprocessing
def _process_chunk_multiprocess(chunk_data: List[Any], start_idx: int) -> Dict[str, HoleData]:
    """Process chunk in separate process"""
    from src.core_business.models.hole_data import HoleData, HoleStatus
    
    holes = {}
    for i, item in enumerate(chunk_data):
        global_idx = start_idx + i
        
        if isinstance(item, dict):
            hole = HoleData(
                hole_id=item.get("id", f"H{global_idx:03d}"),
                center_x=float(item.get("x", global_idx * 10)),
                center_y=float(item.get("y", 50)),
                radius=float(item.get("radius", 5)),
                status=HoleStatus.PENDING
            )
        else:
            hole = HoleData(
                hole_id=f"H{global_idx:03d}",
                center_x=global_idx * 10.0,
                center_y=50.0,
                radius=5.0,
                status=HoleStatus.PENDING
            )
            
        holes[hole.hole_id] = hole
        
    return holes


# Factory function
def create_optimized_data_loader() -> OptimizedDataLoader:
    """Create an optimized data loader instance"""
    return OptimizedDataLoader()