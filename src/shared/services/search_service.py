"""
Search service implementation for business logic layer.

This module handles all search and filtering operations for holes and data.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal

from src.core.exceptions import BusinessControllerError


class SearchService(QObject):
    """
    Service for handling search and filtering operations.
    
    This service provides search functionality for holes, data filtering,
    and result management.
    """
    
    # Signals for search operations
    search_completed = Signal(str, list)  # query, results
    search_failed = Signal(str)  # error_message
    filter_changed = Signal(str, list)  # filter_type, filtered_results
    
    def __init__(self):
        """Initialize the search service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Search state
        self._current_query = ""
        self._current_results: List[str] = []
        self._current_filter = "all"
        self._search_history: List[str] = []
        
        # Data sources
        self._hole_collection: Optional[Any] = None
        self._searchable_data: Dict[str, Any] = {}
        
        self.logger.debug("Search service initialized")
    
    @property
    def current_query(self) -> str:
        """Get the current search query."""
        return self._current_query
    
    @property
    def current_results(self) -> List[str]:
        """Get the current search results."""
        return self._current_results.copy()
    
    @property
    def current_filter(self) -> str:
        """Get the current filter type."""
        return self._current_filter
    
    def set_hole_collection(self, hole_collection: Any) -> None:
        """
        Set the hole collection for searching.
        
        Args:
            hole_collection: Collection of holes to search in
        """
        try:
            self._hole_collection = hole_collection
            self._update_searchable_data()
            self.logger.debug("Hole collection updated for search")
            
        except Exception as e:
            self.logger.error(f"Failed to set hole collection: {e}")
    
    def search(self, query: str) -> List[str]:
        """
        Perform a search with the given query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching hole IDs
        """
        try:
            self.logger.info(f"🔍 开始搜索: '{query}', 可搜索数据: {len(self._searchable_data)} 个孔位")
            
            if not query:
                # Return all holes if no query
                results = list(self._searchable_data.keys())
                self._update_search_state(query, results)
                return results
            
            query = query.strip().lower()
            results = []
            
            # Add to search history
            if query not in self._search_history:
                self._search_history.append(query)
                # Keep only last 20 searches
                self._search_history = self._search_history[-20:]
            
            # Search through all holes
            for hole_id, searchable_fields in self._searchable_data.items():
                if self._matches_query(searchable_fields, query):
                    results.append(hole_id)
            
            # Sort results by relevance
            results = self._sort_results_by_relevance(results, query)
            
            self._update_search_state(query, results)
            self.search_completed.emit(query, results)
            
            self.logger.info(f"✅ 搜索完成: '{query}' -> {len(results)} 个结果")
            if len(results) > 0:
                self.logger.info(f"📋 搜索结果: {results[:10]}")  # 显示前10个结果
            return results
            
        except Exception as e:
            error_msg = f"Search failed: {e}"
            self.logger.error(error_msg)
            self.search_failed.emit(error_msg)
            raise BusinessControllerError(error_msg)
    
    def filter_by_status(self, filter_type: str) -> List[str]:
        """
        Filter holes by status.
        
        Args:
            filter_type: Type of filter ('all', 'pending', 'qualified', 'defective', etc.)
            
        Returns:
            List of filtered hole IDs
        """
        try:
            self._current_filter = filter_type
            
            if filter_type == "all":
                filtered_results = list(self._searchable_data.keys())
            else:
                filtered_results = []
                
                for hole_id, searchable_fields in self._searchable_data.items():
                    hole_status = searchable_fields.get('status', 'unknown').lower()
                    
                    # Map filter types to status values
                    if filter_type == "pending" and hole_status in ['pending', 'waiting', 'todo']:
                        filtered_results.append(hole_id)
                    elif filter_type == "qualified" and hole_status in ['qualified', 'pass', 'ok', 'good']:
                        filtered_results.append(hole_id)
                    elif filter_type == "defective" and hole_status in ['defective', 'fail', 'bad', 'error']:
                        filtered_results.append(hole_id)
                    elif filter_type == "blind" and hole_status in ['blind']:
                        filtered_results.append(hole_id)
                    elif filter_type == "tie_rod" and hole_status in ['tie_rod', 'tie-rod']:
                        filtered_results.append(hole_id)
            
            self.filter_changed.emit(filter_type, filtered_results)
            self.logger.debug(f"Filter applied: '{filter_type}' -> {len(filtered_results)} results")
            
            return filtered_results
            
        except Exception as e:
            error_msg = f"Filter failed: {e}"
            self.logger.error(error_msg)
            self.search_failed.emit(error_msg)
            raise BusinessControllerError(error_msg)
    
    def _update_searchable_data(self) -> None:
        """Update searchable data from hole collection."""
        try:
            self._searchable_data = {}
            
            if not self._hole_collection:
                return
            
            # Extract searchable fields from holes
            holes = []
            if hasattr(self._hole_collection, 'holes'):
                holes = self._hole_collection.holes
            elif hasattr(self._hole_collection, 'get_all_holes'):
                holes = self._hole_collection.get_all_holes()
            elif isinstance(self._hole_collection, list):
                holes = self._hole_collection
            
            for hole in holes:
                hole_id = self._get_hole_id(hole)
                
                # Build searchable data for this hole
                searchable_fields = {
                    'id': hole_id,
                    'status': getattr(hole, 'status', 'unknown'),
                    'position': self._get_hole_position_string(hole),
                    'radius': str(getattr(hole, 'radius', '')),
                    'type': getattr(hole, 'hole_type', 'regular')
                }
                
                # Add any additional searchable attributes
                for attr in ['label', 'name', 'description', 'sector', 'group']:
                    if hasattr(hole, attr):
                        searchable_fields[attr] = str(getattr(hole, attr))
                
                self._searchable_data[hole_id] = searchable_fields
            
            self.logger.info(f"✅ 更新搜索数据: {len(self._searchable_data)} 个孔位")
            if len(self._searchable_data) > 0:
                # 输出前几个孔位ID作为调试信息
                sample_ids = list(self._searchable_data.keys())[:5]
                self.logger.info(f"📋 样本孔位ID: {sample_ids}")
            
        except Exception as e:
            self.logger.error(f"Failed to update searchable data: {e}")
    
    def _matches_query(self, searchable_fields: Dict[str, str], query: str) -> bool:
        """Check if searchable fields match the query."""
        try:
            query_lower = query.lower()
            
            # Check each field for matches
            for field_name, field_value in searchable_fields.items():
                if not field_value:
                    continue
                
                field_value_lower = str(field_value).lower()
                
                # Exact match
                if query_lower == field_value_lower:
                    return True
                
                # Substring match
                if query_lower in field_value_lower:
                    return True
                
                # Pattern matching for specific fields
                if field_name == 'id':
                    # Support patterns like "A1", "B*", etc.
                    if self._matches_id_pattern(field_value_lower, query_lower):
                        return True
                
                # Enhanced fuzzy matching
                if self._fuzzy_match(field_value_lower, query_lower):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error matching query: {e}")
            return False
    
    def _matches_id_pattern(self, hole_id: str, pattern: str) -> bool:
        """Check if hole ID matches a pattern."""
        try:
            # Convert simple patterns to regex
            # * -> .*, ? -> .
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            regex_pattern = f"^{regex_pattern}$"
            
            return bool(re.match(regex_pattern, hole_id))
            
        except Exception as e:
            self.logger.warning(f"Error in pattern matching: {e}")
            return False
    
    def _fuzzy_match(self, text: str, query: str) -> bool:
        """Enhanced fuzzy matching with multiple strategies."""
        try:
            if not text or not query:
                return False
            
            # 1. Character subsequence matching (允许字符间有间隔)
            if self._subsequence_match(text, query):
                return True
            
            # 2. Levenshtein distance based matching (编辑距离)
            if len(query) >= 3 and self._levenshtein_match(text, query):
                return True
                
            # 3. Token-based fuzzy matching (分词匹配)
            if self._token_fuzzy_match(text, query):
                return True
                
            return False
            
        except Exception as e:
            self.logger.warning(f"Error in fuzzy matching: {e}")
            return False
    
    def _subsequence_match(self, text: str, query: str) -> bool:
        """Check if query characters appear in text in order (with gaps allowed)."""
        i = j = 0
        while i < len(text) and j < len(query):
            if text[i] == query[j]:
                j += 1
            i += 1
        return j == len(query)
    
    def _levenshtein_match(self, text: str, query: str) -> bool:
        """Simple Levenshtein distance matching."""
        if abs(len(text) - len(query)) > 2:
            return False
            
        # Simple edit distance calculation
        if len(text) < len(query):
            text, query = query, text
            
        if len(query) == 0:
            return len(text) <= 2
            
        previous_row = list(range(len(query) + 1))
        for i, c1 in enumerate(text):
            current_row = [i + 1]
            for j, c2 in enumerate(query):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        # Allow up to 2 character differences for fuzzy matching
        return previous_row[-1] <= 2
    
    def _token_fuzzy_match(self, text: str, query: str) -> bool:
        """Token-based fuzzy matching for multi-part identifiers."""
        # Split on common separators
        import re
        text_tokens = re.split(r'[-_\s]+', text.lower())
        query_tokens = re.split(r'[-_\s]+', query.lower())
        
        # Check if any query token matches any text token (with prefix matching)
        for query_token in query_tokens:
            if not query_token:
                continue
            for text_token in text_tokens:
                if not text_token:
                    continue
                # Prefix matching or contains matching
                if text_token.startswith(query_token) or query_token in text_token:
                    return True
                    
        return False
    
    def _sort_results_by_relevance(self, results: List[str], query: str) -> List[str]:
        """Sort search results by relevance."""
        try:
            if not results or not query:
                return results
            
            query_lower = query.lower()
            
            def get_relevance_score(hole_id: str) -> int:
                score = 0
                searchable_fields = self._searchable_data.get(hole_id, {})
                
                for field_name, field_value in searchable_fields.items():
                    if not field_value:
                        continue
                    
                    field_value_lower = str(field_value).lower()
                    
                    # Exact match gets highest score
                    if query_lower == field_value_lower:
                        score += 100
                    # ID field matches get higher score
                    elif field_name == 'id' and query_lower in field_value_lower:
                        score += 50
                    # Other field matches
                    elif query_lower in field_value_lower:
                        score += 10
                
                return score
            
            # Sort by relevance score (descending)
            return sorted(results, key=get_relevance_score, reverse=True)
            
        except Exception as e:
            self.logger.warning(f"Error sorting results: {e}")
            return results
    
    def _update_search_state(self, query: str, results: List[str]) -> None:
        """Update internal search state."""
        self._current_query = query
        self._current_results = results
    
    def _get_hole_id(self, hole: Any) -> str:
        """Get hole ID from hole object."""
        if hasattr(hole, 'id'):
            return hole.id
        elif hasattr(hole, 'hole_id'):
            return hole.hole_id
        elif hasattr(hole, 'name'):
            return hole.name
        else:
            return str(hole)
    
    def _get_hole_position_string(self, hole: Any) -> str:
        """Get position string from hole object."""
        try:
            if hasattr(hole, 'position'):
                pos = hole.position
                if hasattr(pos, 'x') and hasattr(pos, 'y'):
                    return f"{pos.x},{pos.y}"
                elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    return f"{pos[0]},{pos[1]}"
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"Error getting hole position: {e}")
            return ""
    
    def debug_search_data(self) -> Dict[str, Any]:
        """调试方法：返回搜索数据的统计信息"""
        return {
            'total_holes': len(self._searchable_data),
            'sample_ids': list(self._searchable_data.keys())[:10],
            'has_hole_collection': self._hole_collection is not None,
            'hole_collection_type': type(self._hole_collection).__name__ if self._hole_collection else None
        }
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        try:
            self._searchable_data.clear()
            self._current_results.clear()
            self._hole_collection = None
            self.logger.debug("Search service cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup search service: {e}")