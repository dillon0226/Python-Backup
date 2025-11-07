# friend_matching_service.py

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Schedule:
    """Represents a student's class schedule"""
    user_id: int
    classes: List[Dict]
    walking_paths: List[List[Tuple[float, float]]]


@dataclass
class FriendSuggestion:
    """Represents a friend suggestion with reasoning"""
    suggested_user_id: int
    score: float
    shared_classes: List[str]
    path_overlap_percent: float
    time_proximity_minutes: int


class FriendMatchingService:
    """Service for matching students based on schedules and walking paths."""
    
    def __init__(self, schedule_repository, connection_repository):
        self.schedule_repo = schedule_repository
        self.connection_repo = connection_repository
        self.MIN_PATH_OVERLAP = 0.30
        self.TIME_PROXIMITY_THRESHOLD = 15
        
    def generate_suggestions(self, user_id: int, limit: int = 10) -> List[FriendSuggestion]:
        """Generate friend suggestions for a user."""
        try:
            user_schedule = self.schedule_repo.get_schedule_by_user(user_id)
            if not user_schedule:
                logger.warning(f"No schedule found for user {user_id}")
                return []
            
            existing_connections = self.connection_repo.get_connections(user_id)
            existing_ids = {conn.other_user_id for conn in existing_connections}
            
            blocked_users = self.connection_repo.get_blocked_users(user_id)
            blocked_ids = {block.blocked_user_id for block in blocked_users}
            
            candidate_schedules = self.schedule_repo.get_schedules_by_university(
                user_schedule.user_id,
                exclude_user_ids=list(existing_ids | blocked_ids | {user_id})
            )
            
            suggestions = []
            
            for candidate_schedule in candidate_schedules:
                suggestion = self._evaluate_match(user_schedule, candidate_schedule)
                if suggestion and suggestion.score > 0:
                    suggestions.append(suggestion)
            
            suggestions.sort(key=lambda x: x.score, reverse=True)
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error generating suggestions for user {user_id}: {str(e)}")
            raise
    
    def _evaluate_match(self, user_schedule: Schedule, 
                       candidate_schedule: Schedule) -> Optional[FriendSuggestion]:
        """Evaluate how well two schedules match."""
        user_classes = {cls['course'] for cls in user_schedule.classes}
        candidate_classes = {cls['course'] for cls in candidate_schedule.classes}
        shared_classes = list(user_classes & candidate_classes)
        
        time_proximity = self._calculate_time_proximity(
            user_schedule.classes, 
            candidate_schedule.classes
        )
        
        path_overlap = self._calculate_path_overlap(
            user_schedule.walking_paths,
            candidate_schedule.walking_paths
        )
        
        score = (
            len(shared_classes) * 0.4 +
            path_overlap * 0.4 +
            (1.0 if time_proximity > 0 else 0) * 0.2
        )
        
        if score < 0.3:
            return None
        
        if len(shared_classes) == 0 and path_overlap < self.MIN_PATH_OVERLAP:
            return None
        
        return FriendSuggestion(
            suggested_user_id=candidate_schedule.user_id,
            score=score,
            shared_classes=shared_classes,
            path_overlap_percent=path_overlap * 100,
            time_proximity_minutes=time_proximity
        )
    
    def _calculate_time_proximity(self, user_classes: List[Dict], 
                                  candidate_classes: List[Dict]) -> int:
        """Calculate minimum time difference between classes."""
        min_diff = float('inf')
        
        for user_class in user_classes:
            user_end = self._parse_time(user_class['end_time'])
            
            for candidate_class in candidate_classes:
                if user_class['day'] != candidate_class['day']:
                    continue
                
                candidate_start = self._parse_time(candidate_class['start_time'])
                diff = abs((candidate_start - user_end).total_seconds() / 60)
                min_diff = min(min_diff, diff)
        
        return int(min_diff) if min_diff <= self.TIME_PROXIMITY_THRESHOLD else -1
    
    def _calculate_path_overlap(self, user_paths: List[List[Tuple[float, float]]], 
                               candidate_paths: List[List[Tuple[float, float]]]) -> float:
        """Calculate percentage of path overlap."""
        if not user_paths or not candidate_paths:
            return 0.0
        
        total_overlap = 0.0
        comparisons = 0
        
        for user_path in user_paths:
            for candidate_path in candidate_paths:
                overlap = self._calculate_single_path_overlap(user_path, candidate_path)
                total_overlap += overlap
                comparisons += 1
        
        return total_overlap / comparisons if comparisons > 0 else 0.0
    
    def _calculate_single_path_overlap(self, path1: List[Tuple[float, float]], 
                                      path2: List[Tuple[float, float]]) -> float:
        """Calculate overlap between two paths."""
        if not path1 or not path2:
            return 0.0
        
        PROXIMITY_THRESHOLD = 0.0005
        overlap_points = 0
        
        for point1 in path1:
            for point2 in path2:
                distance = ((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)**0.5
                if distance < PROXIMITY_THRESHOLD:
                    overlap_points += 1
                    break
        
        return overlap_points / len(path1)
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime object"""
        return datetime.strptime(time_str, "%H:%M")
    
    def create_connection_request(self, requesting_user_id: int, 
                                 target_user_id: int) -> Dict:
        """Create a connection request between two users."""
        try:
            existing = self.connection_repo.get_connection_between(
                requesting_user_id, 
                target_user_id
            )
            if existing:
                raise ValueError("Connection already exists or is pending")
            
            if self._is_blocked(requesting_user_id, target_user_id):
                raise ValueError("Cannot connect with blocked user")
            
            connection = self.connection_repo.create_connection(
                user1_id=requesting_user_id,
                user2_id=target_user_id,
                status='pending',
                suggested_at=datetime.utcnow()
            )
            
            logger.info(f"Connection request: {requesting_user_id} -> {target_user_id}")
            return connection
            
        except Exception as e:
            logger.error(f"Error creating connection request: {str(e)}")
            raise
    
    def accept_connection(self, connection_id: int, accepting_user_id: int) -> Dict:
        """Accept a pending connection request."""
        connection = {'id': connection_id, 'status': 'accepted', 'connected_at': datetime.utcnow()}
        logger.info(f"Connection accepted: {connection_id}")
        return connection
    
    def _is_blocked(self, user1_id: int, user2_id: int) -> bool:
        """Check if either user has blocked the other"""
        return (
            self.connection_repo.is_blocked(user1_id, user2_id) or
            self.connection_repo.is_blocked(user2_id, user1_id)
        )
