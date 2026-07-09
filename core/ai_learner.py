import json
import os
import time

class AILearner:
    def __init__(self, memory_dir="memory"):
        self.memory_dir = memory_dir
        self.log_file = os.path.join(self.memory_dir, "ai_memory.json")
        self.current_run_pattern = []
        
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
                
    def _load_data(self):
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
            
    def _save_data(self, data):
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def start_new_run(self):
        self.current_run_pattern = []
        
    def record_action(self, action, timestamp):
        self.current_run_pattern.append({
            "time": round(timestamp, 2),
            "action": action
        })
        
    def save_run(self, duration, farm_mode, episode='ep1'):
        if duration <= 0:
            return
            
        data = self._load_data()
        if episode not in data:
            data[episode] = {"runs": [], "death_timestamps": []}
            
        # สร้าง record สำหรับรอบนี้
        run_record = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": farm_mode,
            "duration": round(duration, 2),
            "actions": self.current_run_pattern,
            "action_count": len(self.current_run_pattern)
        }
        
        data[episode]["runs"].append(run_record)
        
        # เก็บแค่ 100 รอบล่าสุด
        if len(data[episode]["runs"]) > 100:
            data[episode]["runs"] = data[episode]["runs"][-100:]
            
        # บันทึกสาเหตุการตาย (ดูแอคชั่นสุดท้ายช่วง 1 วินาทีก่อนตาย)
        # ถ้าไม่มีแอคชั่น แปลว่าวิ่งชน (NONE)
        last_action = "NONE"
        for act in reversed(self.current_run_pattern):
            if duration - act["time"] <= 1.0:
                last_action = act["action"]
                break
                
        # เซฟเวลาตายเพื่อใช้เตือนในรอบถัดไป
        data[episode]["death_timestamps"].append({
            "time": round(duration, 2),
            "last_action": last_action
        })
            
        self._save_data(data)

    def reset_memory(self, episode):
        data = self._load_data()
        if episode in data:
            data[episode] = {"runs": [], "death_timestamps": []}
            self._save_data(data)
            
    def get_danger_action(self, current_time, episode):
        data = self._load_data()
        if episode not in data:
            return None
            
        deaths = data[episode].get("death_timestamps", [])
        # เช็คว่าในอนาคตอันใกล้ (0.2 - 0.5 วิข้างหน้า) เคยมีประวัติตายหรือไม่
        for d in deaths:
            time_diff = d["time"] - current_time
            if 0.2 <= time_diff <= 0.5:
                # ถ้าเคยตายตอนทำ NONE ให้ลอง JUMP
                if d["last_action"] == "NONE":
                    return "JUMP"
                # ถ้าเคยตายตอน JUMP ให้ลอง DOUBLE_JUMP
                elif d["last_action"] == "JUMP":
                    return "DOUBLE_JUMP"
                # ถ้าเคยตายตอน DOUBLE_JUMP หรือ SLIDE ให้ลองทำสลับกัน
                elif d["last_action"] == "DOUBLE_JUMP":
                    return "SLIDE"
                else:
                    return "JUMP"
        return None
            
    def get_stats(self):
        data = self._load_data()
        # รวมสถิติทุกด่าน
        total_runs = []
        for ep, ep_data in data.items():
            total_runs.extend(ep_data.get("runs", []))
            
        total_learned = len(total_runs)
        
        best_duration = 0
        latest_pattern = []
        if total_learned > 0:
            best_duration = max([r.get("duration", 0) for r in total_runs])
            # หา run ล่าสุดจากวันที่
            latest_run = sorted(total_runs, key=lambda x: x.get("date", ""), reverse=True)[0]
            latest_pattern = latest_run.get("actions", [])
            
        return {
            "runs": total_runs,
            "total_learned": total_learned,
            "best_duration": best_duration,
            "latest_pattern": latest_pattern
        }
