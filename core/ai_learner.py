import json
import os
import time

class AILearner:
    def __init__(self, memory_dir="memory"):
        self.memory_dir = memory_dir
        self.log_file = os.path.join(self.memory_dir, "run_logs.json")
        self.current_run_pattern = []
        
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump({"runs": []}, f)
                
    def start_new_run(self):
        self.current_run_pattern = []
        
    def record_action(self, action, timestamp):
        # บันทึกแอคชั่นพร้อมเวลา (ทศนิยม 2 ตำแหน่ง)
        self.current_run_pattern.append({
            "time": round(timestamp, 2),
            "action": action
        })
        
    def save_run(self, duration, farm_mode):
        if duration <= 0:
            return
            
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = {"runs": []}
            
        # สร้าง record สำหรับรอบนี้
        run_record = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": farm_mode,
            "duration": round(duration, 2),
            "actions": self.current_run_pattern,
            "action_count": len(self.current_run_pattern)
        }
        
        data["runs"].append(run_record)
        
        # เก็บแค่ 100 รอบล่าสุดเพื่อไม่ให้ไฟล์ใหญ่เกินไป
        if len(data["runs"]) > 100:
            data["runs"] = data["runs"][-100:]
            
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
    def get_stats(self):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            return {"runs": [], "total_learned": 0, "best_duration": 0}
            
        runs = data.get("runs", [])
        total_learned = len(runs)
        
        best_duration = 0
        latest_pattern = []
        if total_learned > 0:
            best_duration = max([r.get("duration", 0) for r in runs])
            latest_pattern = runs[-1].get("actions", [])
            
        return {
            "runs": runs,
            "total_learned": total_learned,
            "best_duration": best_duration,
            "latest_pattern": latest_pattern
        }
