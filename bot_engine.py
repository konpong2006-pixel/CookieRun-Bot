import time
import sys
import threading
import json
import os
from config import *
from core.emulator import get_emulator_window, get_render_window
from core.controller import Controller
from core.vision import Vision
from core.ai_learner import AILearner

class CookieBot:
    def __init__(self):
        self.running = False
        self.current_state = "IDLE"
        self.farm_mode = "COIN" # "COIN" or "BOX"
        self.thread = None
        self.status_msg = "Ready"
        
        # ตั้งค่าที่ปรับแต่งได้ผ่านเว็บ
        self.coin_timeout = 205
        self.box_timeout = 150
        self.use_timeout = True
        self.emulator_title = EMULATOR_WINDOW_TITLE
        
        # ข้อมูลสำหรับ Screen Stream
        self.latest_frame_bytes = None
        self.run_history = []
        self.ai = AILearner()
        self.session_stats = {
            "total_runs": 0,
            "total_box_runs": 0,
            "total_coin_runs": 0,
            "total_coins": 0
        }
        self._load_stats()
        threading.Thread(target=self._screen_capture_loop, daemon=True).start()
        
    def _load_stats(self):
        try:
            if os.path.exists("stats.json"):
                with open("stats.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.session_stats["total_runs"] = data.get("total_runs", 0)
                    self.session_stats["total_box_runs"] = data.get("total_box_runs", 0)
                    self.session_stats["total_coin_runs"] = data.get("total_coin_runs", 0)
                    self.session_stats["total_coins"] = data.get("total_coins", 0)
                    # Load history too if needed
                    history = data.get("run_history", [])
                    self.run_history = history[:20] # Keep max 20
        except Exception as e:
            print(f"Error loading stats: {e}")
            
    def _save_stats(self):
        try:
            data = {
                "total_runs": self.session_stats["total_runs"],
                "total_box_runs": self.session_stats.get("total_box_runs", 0),
                "total_coin_runs": self.session_stats.get("total_coin_runs", 0),
                "total_coins": self.session_stats["total_coins"],
                "run_history": self.run_history
            }
            with open("stats.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def _do_jump(self, controller):
        controller.click_percent(*GAME_JUMP_BTN)

    def _do_double_jump(self, controller):
        controller.double_jump(GAME_JUMP_BTN)

    def _do_slide(self, controller):
        controller.click_percent(*GAME_SLIDE_BTN)

    def start(self, mode="COIN", use_relay=False, use_fast_start=False, episode="ep1"):
        if not self.running:
            self.running = True
            self.farm_mode = mode
            self.use_relay = use_relay
            self.use_fast_start = use_fast_start
            self.episode = episode
            self.current_state = "LOBBY"
            self.ai = AILearner(game_mode=self.farm_mode)
            self.run_start_time = time.time()
            self.status_msg = f"Starting in {mode} mode..."
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        self.current_state = "IDLE"
        self.status_msg = "Stopped by user."

    def get_status(self):
        run_time_str = "00:00"
        if self.running and self.current_state == "GAMEPLAY" and hasattr(self, 'run_start_time') and self.run_start_time:
            elapsed = int(time.time() - self.run_start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            run_time_str = f"{mins:02}:{secs:02}"
            
        return {
            "running": self.running,
            "state": self.current_state,
            "message": self.status_msg,
            "run_time": run_time_str,
            "coin_timeout": self.coin_timeout,
            "box_timeout": self.box_timeout,
            "use_timeout": self.use_timeout,
            "farm_mode": self.farm_mode,
            "emulator_title": self.emulator_title,
            "box_pattern": getattr(self, 'box_pattern', None),
            "coin_pattern": getattr(self, 'coin_pattern', None),
            "run_history": self.run_history,
            "session_stats": self.session_stats
        }

    def reset_stats(self):
        self.session_stats = {
            "total_runs": 0,
            "total_box_runs": 0,
            "total_coin_runs": 0,
            "total_coins": 0
        }
        self.run_history = []
        self._save_stats()
        self.status_msg = "Dashboard data reset."

    def _screen_capture_loop(self):
        import io
        from core.emulator import get_emulator_window, get_render_window
        from core.vision import Vision
        local_vision = None
        last_emulator = None
        while True:
            try:
                if self.emulator_title != last_emulator:
                    local_vision = None
                    last_emulator = self.emulator_title
                    
                if not local_vision:
                    if self.emulator_title == "LDPlayer":
                        r_class, r_title = "RenderWindow", "TheRender"
                    else:
                        r_class, r_title = "subWin", "sub"
                        
                    main_hwnd = get_emulator_window(self.emulator_title)
                    render_hwnd = get_render_window(main_hwnd, r_class, r_title)
                    local_vision = Vision(render_hwnd)
                    
                # แคปจอภาพ 10 ครั้งต่อวินาทีเพื่อส่งเข้าหน้าเว็บแบบ Stream
                img = local_vision.capture_screen()
                if img:
                    # ย่อขนาดลงครึ่งนึงเพื่อให้สตรีมได้ลื่นไหล ไม่หน่วง
                    w, h = img.size
                    img_small = img.resize((w // 2, h // 2))
                    buf = io.BytesIO()
                    img_small.save(buf, format='JPEG', quality=50)
                    self.latest_frame_bytes = buf.getvalue()
            except Exception as e:
                local_vision = None
                print(f"[Screen Capture] Error: {e}")
            time.sleep(0.1)

    def _run_loop(self):
        try:
            self.status_msg = f"Searching for {self.emulator_title}..."
            
            if self.emulator_title == "LDPlayer":
                r_class, r_title = "RenderWindow", "TheRender"
            else:
                r_class, r_title = "subWin", "sub"
                
            main_hwnd = get_emulator_window(self.emulator_title)
            render_hwnd = get_render_window(main_hwnd, r_class, r_title)
            self.status_msg = "Found Emulator Viewport!"

            controller = Controller(render_hwnd)
            vision = Vision(render_hwnd)
            
            global_last_thumb = None
            global_static_frames = 0

            while self.running:
                try:
                    img = vision.capture_screen()
                    
                    # --- Dynamic State Detection ---
                    detected_state = vision.determine_state(img)
                    
                    if self.current_state in ["PREP", "WAIT_FOR_LOBBY"]:
                        # ปิด auto-sync ระหว่างทำ Sequence ที่สำคัญ (เช่น สุ่มกล่อง, หรือ รอเปิดกล่อง)
                        # ป้องกันปัญหาหน้าจอดำตอนโหลดแล้วระบบเข้าใจผิดว่าเป็น GAMEPLAY
                        pass
                    elif self.current_state != "GAMEPLAY":
                        if detected_state in ["LOBBY", "RESULTS", "GAMEPLAY"]:
                            # ป้องกันไม่ให้ State เปลี่ยนกลับไปกลับมาระหว่างรอโหลด
                            if self.current_state != detected_state:
                                self.status_msg = f"State auto-sync: {detected_state}"
                            self.current_state = detected_state
                    elif self.current_state == "GAMEPLAY":
                        # --- Global Desync Recovery ---
                        if detected_state in ["LOBBY", "PREP"]:
                            self.status_msg = f"Desync Detected! Force returning to {detected_state}..."
                            global_static_frames = 0
                            self.current_state = detected_state
                            time.sleep(2)
                            continue
                            
                    # --- Global Watchdog (Anti-Stuck & Auto Recovery) ---
                    # ตรวจจับว่าหน้าจอค้างนิ่งสนิทนานเกินไปหรือไม่ (เช่น หลุดการเชื่อมต่อ, มี Popup โฆษณาเด้งขวาง)
                    w, h = img.size
                    thumb = list(img.crop((int(w*0.4), int(h*0.4), int(w*0.6), int(h*0.6))).resize((8, 8)).getdata())
                    if thumb == global_last_thumb:
                        global_static_frames += 1
                    else:
                        global_static_frames = 0
                        global_last_thumb = thumb
                        
                    # ถ้าภาพนิ่งสนิทเกิน 10 วินาที (100 เฟรม) และไม่ได้อยู่ใน GAMEPLAY (ซึ่งมีระบบจับภาพนิ่งของตัวเองอยู่แล้ว)
                    if global_static_frames > 100 and self.current_state != "GAMEPLAY":
                        self.status_msg = "Anti-Stuck Watchdog: Recovering from frozen state (10s)!"
                        # 1. กดตำแหน่งปุ่ม OK แถวล่าง (ครอบคลุมปุ่มซ้าย กลาง ขวา เลี่ยงรายชื่อเพื่อน)
                        controller.click_percent(35.0, 85.0)
                        time.sleep(0.5)
                        controller.click_percent(50.0, 85.0) # เพิ่มจุดกึ่งกลางสำหรับ Level Up / Daily Reward
                        time.sleep(0.5)
                        controller.click_percent(57.0, 85.0)
                        time.sleep(1)
                        # 2. กดมุมขวาบน (ปิดกากบาทของ Event / Daily Rewards หรือ Popup อื่นๆ)
                        controller.click_percent(90.0, 10.0)
                        time.sleep(1)
                        global_static_frames = 0 # รีเซ็ตแล้วลุยต่อ
                    
                    if self.current_state == "LOBBY":
                        self.status_msg = "Checking Lobby status..."
                        
                        # กดกึ่งกลางหน้าจอ 1 ครั้งเสมอเมื่อเข้า Lobby เพื่อปิด Level Up Popup หรือ Daily Login
                        controller.click_percent(50.0, 75.0)
                        time.sleep(0.5)
                        controller.click_percent(50.0, 85.0)
                        time.sleep(1.0)
                        
                        if self.farm_mode == "BOX_RELIC" and vision.has_get_sign(img, LOBBY_RELIC_GET_AREA):
                            self.status_msg = "Claiming relic..."
                            controller.click_percent(*LOBBY_RELIC_CLAIM)
                            time.sleep(2)
                            controller.click_percent(*POPUP_RELIC_CLAIM_BTN)
                            time.sleep(2)
                            controller.click_percent(*POPUP_RELIC_CLAIM_BTN)
                            time.sleep(2)
                            controller.click_percent(*LOBBY_RELIC_CLOSE)
                            time.sleep(3)
                        
                        self.status_msg = "Pressing Play..."
                        controller.click_percent(*LOBBY_PLAY_BTN)
                        time.sleep(6.0) # รอหน้าต่าง Prep โหลดให้เสร็จสมบูรณ์เผื่อเครื่องช้า
                        self.current_state = "PREP"
                    elif self.current_state == "PREP":
                        time.sleep(2) # รอให้ UI หน้า Prep นิ่ง
                        
                        # นำระบบเช็คว่าค้างอยู่หน้า Lobby ออก เพราะปุ่มมันเขียวและตำแหน่งเดียวกัน ทำให้บอทสับสนและกดเบิ้ล
                            
                        if time.time() - getattr(self, 'last_booster_roll_time', 0) > 60:
                            self.status_msg = f"Rolling Boosters ({self.farm_mode} Mode)..."
                            
                            # 1. กดกล่องสุ่ม
                            controller.click_percent(*PREP_RANDOM_BOOST)
                            time.sleep(1.5)
                            
                            # 2. กดปุ่ม Multi
                            controller.click_percent(*PREP_MULTI_TAB)
                            time.sleep(1)
                            
                            # 3. กด Multi-Buy ใน Popup
                            controller.click_percent(*PREP_MULTI_BUY)
                            
                            # 4. รอให้ระบบสุ่มอัตโนมัติ 15 วินาที
                            self.status_msg = "Waiting 15 seconds for Auto Multi-Buy..."
                            for _ in range(15):
                                if not self.running: break
                                time.sleep(1)
                            
                            self.last_booster_roll_time = time.time()
                            if not self.running: break
                        
                        # 5. กด Stop เผื่อสุ่มไม่เจอ (ถ้าเจอแล้ว ปุ่มนี้คือ Play! จะเป็นการเริ่มเกมเลย)
                        self.status_msg = "Pressing Stop/Play..."
                        controller.click_percent(*PREP_START_GAME)
                        time.sleep(2)
                        
                        # 6. กด Play! ซ้ำอีกรอบเพื่อความชัวร์ (เผื่อเมื่อกี้เป็นการกด Stop)
                        controller.click_percent(*PREP_START_GAME)
                        time.sleep(2)
                            
                        self.current_state = "GAMEPLAY"

                    elif self.current_state == "GAMEPLAY":
                        self.run_start_time = time.time()
                        if hasattr(self, 'ai'):
                            self.ai.start_new_run()
                        
                        last_jump_time = time.time()
                        relay_used = False
                        game_over_timer = 0
                        last_middle_click_time = time.time()
                        
                        # ตัวแปรจับความเคลื่อนไหว
                        last_motion_thumb = None
                        static_frames = 0
                        
                        import random
                        self.box_pattern = random.choice(["RABBIT_JUMP", "SNAKE_SLIDE", "NINJA_DASH", "SAFE_GUARD"]) if self.farm_mode == "BOX" else None
                        self.coin_pattern = random.choice(["AGILE_JUMPER", "SMART_SLIDER", "BALANCE_WALKER", "GROUND_LOVER"]) if self.farm_mode == "COIN" else None
                        
                        while self.running:
                            img = vision.capture_screen()
                            
                            # [Hybrid Detection] ระบบที่ 2: Motion Detection (เช็คภาพจิ๋วมุมซ้ายบน)
                            w, h = img.size
                            thumb = list(img.crop((int(w*0.1), int(h*0.2), int(w*0.3), int(h*0.4))).resize((8, 8)).getdata())
                            if thumb == last_motion_thumb:
                                static_frames += 1
                            else:
                                static_frames = 0
                                last_motion_thumb = thumb
                                

                            # ป้องกันเผลอกดปุ่มซื้อเพชร (หน้าต่างชุบชีวิต) หรือเผลอกดตอนเกมค้าง
                            if static_frames > 5:
                                # ถ้าพึ่งเริ่มเกม (ไม่เกิน 15 วินาที) แล้วภาพยังนิ่ง แปลว่าอยู่ในหน้าโหลด
                                if time.time() - self.run_start_time < 15.0:
                                    self.status_msg = "Loading..."
                                    time.sleep(0.5)
                                    continue
                                
                                # ตรวจสอบว่าเป็นหน้าจบเกมหรือไม่ (เช็คเฉพาะตอนภาพนิ่งเพื่อป้องกันการอ่านสีผิดพลาดตอนวิ่ง)
                                if vision.is_result_screen(img):
                                    run_duration = time.time() - self.run_start_time
                                    self.status_msg = f"Game Over! Run lasted {run_duration:.1f}s."
                                    if hasattr(self, 'ai'):
                                        self.ai.on_death(time.time())
                                    time.sleep(1)
                                    self.current_state = "RESULTS"
                                    break
                                
                                
                                # เช็คปุ่มไม้ผลัด (ใช้ได้กับทุกโหมดถ้าเปิดใช้งาน)
                                if self.use_relay and not relay_used and vision.is_relay_window(img, RELAY_SCAN_AREA):
                                    self.status_msg = "Relaying to Cookie 2..."
                                    time.sleep(1.0) # รอให้ปุ่มแสดงผลจนจบอนิเมชั่น
                                    controller.click_percent(*GAME_RELAY_COOKIE)
                                    time.sleep(0.5)
                                    controller.click_percent(*GAME_RELAY_COOKIE) # กดย้ำอีกครั้งเพื่อความชัวร์
                                    relay_used = True
                                    static_frames = 0
                                    time.sleep(2)
                                    continue

                                self.status_msg = "Screen paused/popup detected. Halting actions..."
                                
                                # ถ้าค้างนานเกิน 8 วินาที (และเล่นมาเกิน 20 วินาทีแล้ว) แปลว่าอยู่หน้าจบเกมแน่นอน
                                if static_frames > 80:
                                    if time.time() - self.run_start_time > 20.0:
                                        self.status_msg = "Run completed. Result screen detected (Motion)!"
                                        if hasattr(self, 'ai'):
                                            self.ai.on_death(time.time())
                                        self.current_state = "RESULTS"
                                        break
                                    
                                game_over_timer += 1
                                time.sleep(0.1)
                                continue
                                
                            self.status_msg = "Running in stage..."
                            
                            time_in_run = time.time() - self.run_start_time
                            if getattr(self, 'use_fast_start', False) and time_in_run < 5.0:
                                controller.click_percent(50.0, 50.0)
                            else:
                                if time.time() - last_middle_click_time >= 3.5:
                                    controller.click_percent(50.0, 50.0)
                                    last_middle_click_time = time.time()
                            
                            # Extract AI Features
                            current_features = vision.extract_obstacle_features(img)
                            current_action = "IDLE"
                            
                            # ตรวจสอบ AI Danger Prediction V2
                            ai_overridden = False
                            if hasattr(self, 'ai') and current_features is not None:
                                prediction = self.ai.predict_danger(current_features)
                                if prediction and prediction["confidence"] >= 0.80:
                                    ai_overridden = True
                                    danger_action = prediction["action"]
                                    self.status_msg = f"[AI] {prediction['confidence']*100:.0f}% MATCH -> {danger_action}"
                                    
                                    current_action = danger_action
                                    if danger_action == "JUMP":
                                        self._do_jump(controller)
                                        last_jump_time = time.time()
                                    elif danger_action == "DOUBLE_JUMP":
                                        self._do_double_jump(controller)
                                        last_jump_time = time.time()
                                    elif danger_action == "SLIDE":
                                        self._do_slide(controller)
                                        
                                    time.sleep(0.1)
                                    
                            if not ai_overridden and self.farm_mode == "COIN":
                                # ระบบตาเลเซอร์สแกนสภาพแวดล้อม (Fallback)
                                env_state = vision.scan_environment(img)
                                
                                if env_state == "POTATO_SKILL":
                                    self.status_msg = "Potato Skill! Single Short Jump!"
                                    if time.time() - last_jump_time > 0.35:
                                        current_action = "JUMP"
                                        self._do_jump(controller)
                                        last_jump_time = time.time()
                                elif env_state == "HOLE":
                                    self.status_msg = "Hole detected! Double Jump!"
                                    current_action = "DOUBLE_JUMP"
                                    self._do_double_jump(controller)
                                    last_jump_time = time.time()
                                    time.sleep(0.1)
                                elif env_state == "OBSTACLE_LOW":
                                    self.status_msg = "Low Obstacle! Jump!"
                                    current_action = "JUMP"
                                    self._do_jump(controller)
                                    last_jump_time = time.time()
                                    time.sleep(0.1)
                                elif env_state == "OBSTACLE_HIGH":
                                    self.status_msg = "High Obstacle! Slide!"
                                    current_action = "SLIDE"
                                    self._do_slide(controller)
                                    time.sleep(0.2)
                                else:
                                    self.status_msg = f"Safe... ({self.coin_pattern})"
                                    if time.time() - last_jump_time > JUMP_INTERVAL:
                                        if self.coin_pattern == "AGILE_JUMPER":
                                            if random.random() > 0.5:
                                                current_action = "DOUBLE_JUMP"
                                                self._do_double_jump(controller)
                                            else:
                                                current_action = "JUMP"
                                                self._do_jump(controller)
                                        elif self.coin_pattern == "SMART_SLIDER":
                                            if random.random() > 0.2:
                                                current_action = "SLIDE"
                                                self._do_slide(controller)
                                                time.sleep(0.3)
                                            else:
                                                current_action = "JUMP"
                                                self._do_jump(controller)
                                        elif self.coin_pattern == "BALANCE_WALKER":
                                            r = random.random()
                                            if r < 0.33:
                                                current_action = "DOUBLE_JUMP"
                                                self._do_double_jump(controller)
                                            elif r < 0.66:
                                                current_action = "JUMP"
                                                self._do_jump(controller)
                                            else:
                                                current_action = "SLIDE"
                                                self._do_slide(controller)
                                                time.sleep(0.2)
                                        else: # GROUND_LOVER
                                            if random.random() > 0.1:
                                                current_action = "SLIDE"
                                                self._do_slide(controller)
                                                time.sleep(0.4)
                                            else:
                                                current_action = "JUMP"
                                                self._do_jump(controller)
                            elif not ai_overridden:
                                # BOX Mode: Anti-Macro Movements 
                                if self.box_pattern == "RABBIT_JUMP":
                                    if time.time() - last_jump_time > random.uniform(1.0, 3.0):
                                        self.status_msg = "Anti-Macro (RABBIT_JUMP): Jump!"
                                        if random.random() > 0.7:
                                            current_action = "DOUBLE_JUMP"
                                            self._do_double_jump(controller)
                                        else:
                                            current_action = "JUMP"
                                            self._do_jump(controller)
                                        last_jump_time = time.time()
                                elif self.box_pattern == "SNAKE_SLIDE":
                                    if time.time() - last_jump_time > random.uniform(2.5, 5.0):
                                        if random.random() > 0.2:
                                            self.status_msg = "Anti-Macro (SNAKE_SLIDE): Slide!"
                                            current_action = "SLIDE"
                                            self._do_slide(controller)
                                            time.sleep(0.5)
                                        else:
                                            self.status_msg = "Anti-Macro (SNAKE_SLIDE): Jump!"
                                            current_action = "JUMP"
                                            self._do_jump(controller)
                                        last_jump_time = time.time()
                                elif self.box_pattern == "NINJA_DASH":
                                    if time.time() - last_jump_time > random.uniform(1.5, 3.0):
                                        self.status_msg = "Anti-Macro (NINJA_DASH): Fast Jump!"
                                        if random.random() > 0.2:
                                            current_action = "JUMP"
                                            self._do_jump(controller)
                                        else:
                                            current_action = "DOUBLE_JUMP"
                                            self._do_double_jump(controller)
                                        last_jump_time = time.time()
                                else: # SAFE_GUARD
                                    if time.time() - last_jump_time > random.uniform(4.0, 7.0):
                                        self.status_msg = "Anti-Macro (SAFE_GUARD): Safe Slide!"
                                        current_action = "SLIDE"
                                        self._do_slide(controller)
                                        time.sleep(0.3)
                                        last_jump_time = time.time()
                                        
                            if hasattr(self, 'ai'):
                                self.ai.add_frame(time.time(), current_features, current_action)
                                    
                            # เงื่อนไขออกจากลูป Gameplay ไปยัง Result
                            # บังคับจบเกมตามเวลาที่ตั้งค่าไว้ (Timer)
                            if self.use_timeout and hasattr(self, 'run_start_time') and self.run_start_time:
                                current_run_time = time.time() - self.run_start_time
                                if self.farm_mode in ["BOX", "BOX_RELIC"]:
                                    current_timeout = self.box_timeout
                                    if current_run_time > current_timeout:
                                        self.status_msg = f"Time Limit Reached ({current_timeout}s). Forcing Result!"
                                        self.current_state = "RESULTS"
                                        break
                                else:
                                    current_timeout = self.coin_timeout
                                    if current_run_time > current_timeout:
                                        self.status_msg = f"Time Limit Reached ({current_timeout}s). Forcing Result!"
                                        self.current_state = "RESULTS"
                                        break
                            
                            # (ย้ายส่วนตรวจสอบ Result ไปไว้ด้านบนแล้ว)
                            
                            if static_frames > 80:  # ถ้านิ่งสนิทนาน 8 วินาที แปลว่าอยู่หน้าจบเกมแน่นอน
                                self.status_msg = "Run completed. Result screen detected (Motion)!"
                                self.current_state = "RESULTS"
                                break
                                
                            game_over_timer += 1
                                
                            time.sleep(0.1)
                            
                        if not self.running: break
                        
                        # บันทึกประวัติ
                        elapsed = int(time.time() - self.run_start_time)
                        mins = elapsed // 60
                        secs = elapsed % 60
                        duration_str = f"{mins:02}:{secs:02}"
                        
                        pattern_used = getattr(self, 'box_pattern', None) if self.farm_mode == "BOX" else getattr(self, 'coin_pattern', None)
                        self.run_history.insert(0, {
                            "time": f"⏱️ {duration_str}",
                            "mode": self.farm_mode,
                            "pattern": pattern_used or "NONE",
                            "coins": 0 # จะถูกอัปเดตใน RESULTS
                        })
                        if len(self.run_history) > 20: # เก็บประวัติให้ยาวขึ้นสำหรับ Dashboard
                            self.run_history.pop()
                            
                        self.current_state = "RESULTS"

                    elif self.current_state == "RESULTS":
                        self.status_msg = "Result screen detected! Waiting for coin tally..."
                        time.sleep(2) # รอให้ตัวเลขเหรียญวิ่งจนจบ
                        
                        # อ่านจำนวนเหรียญ
                        result_img = vision.capture_screen()
                        coins_earned = vision.read_coins_result(result_img)
                        self.session_stats["total_runs"] += 1
                        if self.farm_mode == "BOX":
                            self.session_stats["total_box_runs"] += 1
                        else:
                            self.session_stats["total_coin_runs"] += 1
                            
                        self.session_stats["total_coins"] += coins_earned
                        
                        if len(self.run_history) > 0:
                            self.run_history[0]["coins"] = coins_earned
                            
                        self._save_stats() # บันทึกลงไฟล์
                        
                        self.status_msg = f"Earned {coins_earned} coins! Clicking OK..."
                        
                        # กดปุ่ม OK หน้า Result (จุด X=35.0 จะโดนปุ่ม OK เสมอ ไม่ว่าจะมีปุ่ม Show Off หรือไม่)
                        # ห้ามกด X=57.0 เด็ดขาดเพราะจะไปโดนปุ่ม Show Off (สีฟ้า)
                        time.sleep(1.5)
                        controller.click_percent(35.0, 85.0)
                        
                        # รอให้หน้า Result หายไป เพื่อป้องกันการกดพลาดตอนโหลด
                        time.sleep(4)
                        
                        self.status_msg = "Transitioning to Lobby..."
                        self.current_state = "WAIT_FOR_LOBBY"
                        
                    elif self.current_state == "WAIT_FOR_LOBBY":
                        # ระบบนี้จะทำงานจนกว่าจะเห็นปุ่ม Play! สีเขียวในหน้า Lobby จริงๆ (เปลี่ยน state อัตโนมัติจาก Dynamic State)
                        if vision.is_center_popup_button(img):
                            self.status_msg = "Popup/Box detected! Clicking..."
                            # กด 2 จุด: X=35 (เผื่อมีปุ่ม Open All โผล่มาฝั่งซ้าย) และ X=50 (ปุ่ม Confirm หรือ Open กล่องเดียวตรงกลาง)
                            controller.click_percent(35.0, 85.0)
                            time.sleep(1.5)
                            controller.click_percent(50.0, 85.0)
                            time.sleep(5.5)
                        elif vision.is_lobby_screen(img):
                            self.status_msg = "Lobby ready. Checking for dropping boxes..."
                            time.sleep(4.0) # รอให้กล่องหล่นลงมาจนเสร็จ (ถ้ามี)
                            img_check = vision.capture_screen()
                            if vision.is_center_popup_button(img_check):
                                self.status_msg = "Box dropped after lobby! Clicking..."
                                controller.click_percent(35.0, 85.0)
                                time.sleep(1.5)
                                controller.click_percent(50.0, 85.0)
                                time.sleep(5.5)
                            else:
                                self.current_state = "LOBBY"
                        else:
                            self.status_msg = "Waiting for Lobby or Popups..."
                            time.sleep(1) # รอเฉยๆ อย่างปลอดภัย!

                except Exception as e:
                    self.status_msg = f"Error: {e}"
                    time.sleep(3)

        except Exception as ex:
            self.running = False
            self.current_state = "ERROR"
            self.status_msg = f"Fatal Error: {ex}"

# Singleton instance สำหรับถูกเรียกใช้จาก Server
bot_instance = CookieBot()
