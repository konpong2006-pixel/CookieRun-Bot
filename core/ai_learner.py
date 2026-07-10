import json
import os
import time
import uuid
from collections import deque
import numpy as np

class AILearner:
    def __init__(self, game_mode="COIN", memory_dir="memory"):
        self.memory_dir = memory_dir
        self.game_mode = game_mode
        self.log_file = os.path.join(self.memory_dir, f"visual_memory_{self.game_mode}.json")
        
        # Rolling frame buffer (approx 9 seconds at 10 FPS)
        self.buffer = deque(maxlen=90)
        
        # In-memory database of patterns
        self.memory_db = self._load_data()
        
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
    def _load_data(self):
        if not os.path.exists(self.log_file):
            return self._create_empty_db()
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert feature_vectors back to numpy arrays for fast compute
                for p in data.get("patterns", []):
                    p["feature_vector"] = np.array(p["feature_vector"], dtype=np.float32)
                return data
        except Exception as e:
            print(f"[AILearner] Error loading memory: {e}")
            return self._create_empty_db()
            
    def _create_empty_db(self):
        return {
            "metadata": {
                "version": "2.0",
                "game_mode": self.game_mode,
                "last_updated": time.time(),
                "total_patterns": 0,
                "total_deaths": 0
            },
            "patterns": []
        }
            
    def _save_data(self):
        try:
            # Need to convert numpy arrays to lists before JSON serialization
            data_to_save = json.loads(json.dumps(self.memory_db, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x))
            data_to_save["metadata"]["last_updated"] = time.time()
            data_to_save["metadata"]["total_patterns"] = len(self.memory_db["patterns"])
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            print(f"[AILearner] Error saving memory: {e}")

    def start_new_run(self):
        self.buffer.clear()
        
    def add_frame(self, timestamp, features, action, state="GAMEPLAY"):
        """Add frame to rolling buffer."""
        if features is None:
            return
            
        self.buffer.append({
            "timestamp": round(timestamp, 2),
            "feature_vector": features,
            "action_taken": action,
            "game_state": state
        })
        
    def on_death(self, death_timestamp):
        """Analyze death and update memory."""
        if len(self.buffer) == 0:
            return
            
        self.memory_db["metadata"]["total_deaths"] += 1
        
        # Look back ~1.0 to 1.5 seconds (10-15 frames) to find the critical moment
        # We will iterate backwards from the buffer
        buffer_list = list(self.buffer)
        
        # Find the frame closest to (death_timestamp - 1.2)
        target_time = death_timestamp - 1.2
        
        critical_frame = None
        min_diff = float('inf')
        
        for frame in buffer_list:
            diff = abs(frame["timestamp"] - target_time)
            if diff < min_diff:
                min_diff = diff
                critical_frame = frame
                
        if not critical_frame:
            critical_frame = buffer_list[-1] # Fallback to last known frame
            
        failed_action = critical_frame["action_taken"]
        if failed_action == "NONE": 
            failed_action = "IDLE" # Standardize name
            
        critical_features = critical_frame["feature_vector"]
        
        # Pattern Matching
        closest_pattern = None
        min_dist = float('inf')
        
        for p in self.memory_db["patterns"]:
            dist = np.linalg.norm(p["feature_vector"] - critical_features)
            if dist < min_dist:
                min_dist = dist
                closest_pattern = p
                
        DISTANCE_THRESHOLD = 0.5  # Tunable threshold
        
        if closest_pattern and min_dist < DISTANCE_THRESHOLD:
            # Update existing pattern
            closest_pattern["occurrences"] += 1
            closest_pattern["last_seen"] = time.time()
            if failed_action in closest_pattern["action_outcomes"]:
                closest_pattern["action_outcomes"][failed_action]["death"] += 1
            
            self._update_recommended_action(closest_pattern)
        else:
            # Create new pattern
            new_pattern = {
                "id": f"pattern_{uuid.uuid4().hex[:8]}",
                "feature_vector": critical_features,
                "created_at": time.time(),
                "last_seen": time.time(),
                "occurrences": 1,
                "action_outcomes": {
                    "JUMP": {"success": 0, "death": 0, "neutral": 0},
                    "SLIDE": {"success": 0, "death": 0, "neutral": 0},
                    "DOUBLE_JUMP": {"success": 0, "death": 0, "neutral": 0},
                    "IDLE": {"success": 0, "death": 0, "neutral": 0}
                },
                "recommended_action": "JUMP", # Default guess
                "confidence": 0.5
            }
            # Mark the failed action
            if failed_action in new_pattern["action_outcomes"]:
                new_pattern["action_outcomes"][failed_action]["death"] += 1
                
            self._update_recommended_action(new_pattern)
            self.memory_db["patterns"].append(new_pattern)
            
        self._save_data()
        
    def _update_recommended_action(self, pattern):
        """Determine best action based on historical outcomes."""
        outcomes = pattern["action_outcomes"]
        
        # Scoring logic: Success is good, Death is very bad
        best_action = "JUMP"
        highest_score = -9999
        
        for action, stats in outcomes.items():
            # Simple heuristic
            score = (stats["success"] * 2) - (stats["death"] * 5)
            
            # If an action has NEVER been tried, give it a slight positive score to encourage exploration
            if stats["success"] == 0 and stats["death"] == 0:
                score = 1
                
            if score > highest_score:
                highest_score = score
                best_action = action
                
        pattern["recommended_action"] = best_action
        
        # Calculate confidence based on how many times we've tried actions
        total_attempts = sum(s["success"] + s["death"] for s in outcomes.values())
        if total_attempts > 0:
            pattern["confidence"] = min(0.95, 0.5 + (total_attempts * 0.05))
        else:
            pattern["confidence"] = 0.5

    def predict_danger(self, feature_vector):
        """Find matching patterns and recommend action."""
        if len(self.memory_db["patterns"]) == 0 or feature_vector is None:
            return None
            
        min_dist = float('inf')
        closest_pattern = None
        
        for p in self.memory_db["patterns"]:
            dist = np.linalg.norm(p["feature_vector"] - feature_vector)
            if dist < min_dist:
                min_dist = dist
                closest_pattern = p
                
        # Cosine similarity is usually 1 - cosine_distance. Using Euclidean for now as per spec
        # You may want to tune DISTANCE_THRESHOLD based on actual vector magnitudes
        DISTANCE_THRESHOLD = 0.5
        
        if min_dist < DISTANCE_THRESHOLD:
            # Normalize distance to a 0-1 confidence score modifier
            sim_score = max(0, 1.0 - (min_dist / DISTANCE_THRESHOLD))
            final_confidence = closest_pattern["confidence"] * sim_score
            
            return {
                "action": closest_pattern["recommended_action"],
                "confidence": final_confidence,
                "pattern_id": closest_pattern["id"]
            }
            
        return None
        
    # Legacy methods for compatibility if needed elsewhere
    def get_stats(self):
        return {
            "runs": [],
            "total_learned": self.memory_db["metadata"]["total_patterns"],
            "best_duration": 0,
            "latest_pattern": []
        }
    
    def get_danger_action(self, current_time, episode):
        # Disabled in V2, prediction happens real-time via predict_danger
        return None
        
    def save_run(self, duration, farm_mode, episode='ep1'):
        # In V2, saving is triggered dynamically on death
        pass
    
    def record_action(self, action, timestamp):
        # Handled in add_frame now
        pass
