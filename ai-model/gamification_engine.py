import numpy as np
from enum import Enum

class WasteType(Enum):
    PLASTIC = "plastic"
    PAPER = "paper"
    METAL = "metal"
    ORGANIC = "organic"

class GamificationEngine:
    """Rule-based gamification system"""
    
    def __init__(self):
        self.points_per_classification = 10
        self.level_thresholds = [0, 100, 300, 600, 1000, 1500]
        self.ranks = ["Novice", "Apprentice", "Expert", "Master", "Legendary"]
        
        # Badge definitions
        self.badges = {
            'first_classification': {
                'name': 'First Step',
                'description': 'Classify your first item',
                'condition': lambda stats: stats['total_classifications'] >= 1,
                'icon': '🎯'
            },
            'ten_classifications': {
                'name': 'Active Recycler',
                'description': 'Classify 10 items',
                'condition': lambda stats: stats['total_classifications'] >= 10,
                'icon': '♻️'
            },
            'fifty_classifications': {
                'name': 'Eco Warrior',
                'description': 'Classify 50 items',
                'condition': lambda stats: stats['total_classifications'] >= 50,
                'icon': '🌍'
            },
            'hundred_classifications': {
                'name': 'Planet Protector',
                'description': 'Classify 100 items',
                'condition': lambda stats: stats['total_classifications'] >= 100,
                'icon': '🛡️'
            },
            'collector_plastic': {
                'name': 'Plastic Collector',
                'description': 'Classify 20 plastic items',
                'condition': lambda stats: stats.get('plastic_count', 0) >= 20,
                'icon': '🔴'
            },
            'collector_paper': {
                'name': 'Paper Collector',
                'description': 'Classify 20 paper items',
                'condition': lambda stats: stats.get('paper_count', 0) >= 20,
                'icon': '📄'
            },
            'collector_metal': {
                'name': 'Metal Collector',
                'description': 'Classify 20 metal items',
                'condition': lambda stats: stats.get('metal_count', 0) >= 20,
                'icon': '⚙️'
            },
            'collector_organic': {
                'name': 'Organic Collector',
                'description': 'Classify 20 organic items',
                'condition': lambda stats: stats.get('organic_count', 0) >= 20,
                'icon': '🍂'
            },
        }
    
    def calculate_points(self, waste_type: WasteType, confidence: float) -> int:
        """Calculate points based on waste type and model confidence"""
        base_points = self.points_per_classification
        confidence_bonus = int(confidence * 10)  # 0-10 bonus points
        return base_points + confidence_bonus
    
    def get_level(self, points: int) -> int:
        """Get user level based on points"""
        for level, threshold in enumerate(self.level_thresholds):
            if points < threshold:
                return level
        return len(self.level_thresholds)
    
    def get_rank(self, level: int) -> str:
        """Get rank name from level"""
        if level >= len(self.ranks):
            return self.ranks[-1]
        return self.ranks[level]
    
    def check_badges(self, user_stats: dict) -> list:
        """Check which badges should be unlocked"""
        unlocked = []
        for badge_id, badge_info in self.badges.items():
            if badge_info['condition'](user_stats):
                unlocked.append({
                    'id': badge_id,
                    'name': badge_info['name'],
                    'description': badge_info['description'],
                    'icon': badge_info['icon']
                })
        return unlocked
    
    def process_classification(self, user_id: str, waste_type: WasteType, 
                             confidence: float, user_stats: dict) -> dict:
        """Process a classification and return updated stats"""
        
        points = self.calculate_points(waste_type, confidence)
        
        # Update stats
        new_stats = user_stats.copy()
        new_stats['points'] = user_stats.get('points', 0) + points
        new_stats['total_classifications'] = user_stats.get('total_classifications', 0) + 1
        
        # Track by waste type
        waste_key = f"{waste_type.value}_count"
        new_stats[waste_key] = user_stats.get(waste_key, 0) + 1
        
        # Update level and rank
        new_stats['level'] = self.get_level(new_stats['points'])
        new_stats['rank'] = self.get_rank(new_stats['level'])
        
        # Check badges
        new_stats['badges'] = self.check_badges(new_stats)
        
        return {
            'points_earned': points,
            'updated_stats': new_stats,
            'new_badges': self._get_new_badges(user_stats, new_stats)
        }
    
    def _get_new_badges(self, old_stats: dict, new_stats: dict) -> list:
        """Find newly unlocked badges"""
        old_badges = set(b['id'] for b in old_stats.get('badges', []))
        new_badges = set(b['id'] for b in new_stats.get('badges', []))
        newly_unlocked = new_badges - old_badges
        
        return [b for b in new_stats['badges'] if b['id'] in newly_unlocked]
    
    def get_leaderboard(self, users_stats: list, limit: int = 10) -> list:
        """Generate leaderboard from user stats"""
        sorted_users = sorted(users_stats, key=lambda x: x['points'], reverse=True)
        return [
            {
                'rank': i + 1,
                'user_id': user['user_id'],
                'points': user['points'],
                'level': user.get('level', 1),
                'rank_name': user.get('rank', 'Novice')
            }
            for i, user in enumerate(sorted_users[:limit])
        ]

# Example usage
if __name__ == "__main__":
    engine = GamificationEngine()
    
    # Simulate user classification
    user_stats = {
        'user_id': 'user123',
        'points': 0,
        'total_classifications': 0,
        'plastic_count': 0,
        'level': 1,
        'rank': 'Novice',
        'badges': []
    }
    
    result = engine.process_classification(
        'user123',
        WasteType.PLASTIC,
        0.95,
        user_stats
    )
    
    print(f"Points earned: {result['points_earned']}")
    print(f"Updated stats: {result['updated_stats']}")
    print(f"New badges: {result['new_badges']}")
