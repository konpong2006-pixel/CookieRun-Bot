import time
import sys
import threading
import json
import os
from config import *
from core.emulator import get_emulator_window, get_render_window
from core.controller import Controller
from core.vision import Vision

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
        
        # ข้อมูลสำหรับ Screen Stream
        self.latest_frame_bytes = None
        self.run_history = []
        self.session_stats = {
            "total_runs": 0,
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
                "total_coins": self.session_stats["total_coins"],
                "run_history": self.run_history
            }
            with open("stats.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def start(self, mode="COIN"):
        if not self.running:
            self.running = True
            self.farm_mode = mode
            self.current_state = "LOBBY"
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
        while True:
            try:
                if not local_vision:
                    main_hwnd = get_emulator_window(EMULATOR_WINDOW_TITLE)
                    render_hwnd = get_render_window(main_hwnd, EMULATOR_RENDER_CLASS, EMULATOR_RENDER_TITLE)
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
            except Exception:
                local_vision = None
            time.sleep(0.1)

    def _run_loop(self):
        try:
            self.status_msg = f"Searching for {EMULATOR_WINDOW_TITLE}..."
            main_hwnd = get_emulator_window(EMULATOR_WINDOW_TITLE)
            render_hwnd = get_render_window(main_hwnd, EMULATOR_RENDER_CLASS, EMULATOR_RENDER_TITLE)
            self.status_msg = "Found Emulator Viewport!"

            controller = Controller(render_hwnd)
            vision = Vision(render_hwnd)
            
            global_last_thumb = None
            global_static_frames = 0

            while self.running:
                try:
                    img = vision.capture_screen()
                    
                    # --- Global Desync Recovery ---
                    # หากบอทคิดว่ากำลังวิ่งอยู่ (GAMEPLAY) หรืออยู่หน้า Result แต่ดันตรวจพบปุ่ม Play! ของหน้าหลัก
                    # แปลว่าเกิดการวืดกดไม่ติด หรือเกมเด้งกลับมาหน้าหลัก ให้ทำการรีเซ็ต State กลับไปเริ่มใหม่
                    if self.current_state in ["GAMEPLAY", "RESULTS"]:
                        if vision.is_lobby_screen(img):
                            self.status_msg = "Desync Detected! Force returning to LOBBY..."
                            global_static_frames = 0
                            self.current_state = "LOBBY"
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
                        # 1. กดตำแหน่งปุ่ม OK แถวล่าง (เลี่ยงจุดที่ตรงกับรายชื่อเพื่อน)
                        controller.click_percent(35.0, 85.0)
                        time.sleep(0.5)
                        controller.click_percent(57.0, 85.0)
                        time.sleep(1)
                        # 2. กดมุมขวาบน (ปิดกากบาทของ Event / Daily Rewards หรือ Popup อื่นๆ)
                        controller.click_percent(90.0, 10.0)
                        time.sleep(1)
                        global_static_frames = 0 # รีเซ็ตแล้วลุยต่อ
                    
                    if self.current_state == "LOBBY":
                        self.status_msg = "Checking Lobby status..."
                        
                        if vision.has_get_sign(img, LOBBY_RELIC_GET_AREA):
                            self.status_msg = "Claiming relic..."
                            controller.click_percent(*LOBBY_RELIC_CLAIM)
                            time.sleep(2)
                            controller.click_percent(*LOBBY_RELIC_CLOSE)
                            time.sleep(1)
                        
                        self.status_msg = "Pressing Play..."
                        controller.click_percent(*LOBBY_PLAY_BTN)
                        time.sleep(3) # รอหน้าต่าง Prep โหลด
                        self.current_state = "PREP"

                    elif self.current_state == "PREP":
                        time.sleep(1) # รอให้ UI หน้า Prep นิ่ง
                        if self.farm_mode == "COIN":
                            self.status_msg = "Rolling Boosters (COIN Mode)..."
                            
                            # 1. กดกล่องสุ่ม
                            controller.click_percent(*PREP_RANDOM_BOOST)
                            time.sleep(1)
                            
                            # 2. กดปุ่ม Multi
                            controller.click_percent(*PREP_MULTI_TAB)
                            time.sleep(1)
                            
                            # 3. กด Multi-Buy ใน Popup
                            controller.click_percent(*PREP_MULTI_BUY)
                            
                            # 4. รอให้ระบบสุ่มอัตโนมัติ 20 วินาที
                            self.status_msg = "Waiting 20 seconds for Auto Multi-Buy..."
                            for _ in range(20):
                                if not self.running: break
                                time.sleep(1)
                            if not self.running: break
                            
                            # 5. กด Stop เผื่อสุ่มไม่เจอ (ถ้าเจอแล้ว ปุ่มนี้คือ Play! จะเป็นการเริ่มเกมเลย)
                            self.status_msg = "Pressing Stop/Play..."
                            controller.click_percent(*PREP_START_GAME)
                            time.sleep(2)
                            
                            # 6. กด Play! ซ้ำอีกรอบเพื่อความชัวร์ (เผื่อเมื่อกี้เป็นการกด Stop)
                            controller.click_percent(*PREP_START_GAME)
                            time.sleep(2)
                        else:
                            # BOX Mode ไม่ต้องสุ่ม เริ่มเกม
                            self.status_msg = "Starting Game..."
                            controller.click_percent(*PREP_START_GAME)
                            time.sleep(1)
                            # กดย้ำอีกทีเพื่อความชัวร์ เผื่อดีเลย์
                            controller.click_percent(*PREP_START_GAME)
                            time.sleep(5) # รอโหลดเข้าด่าน
                            
                        self.current_state = "GAMEPLAY"

                    elif self.current_state == "GAMEPLAY":
                        self.status_msg = "Loading... Spamming Fast Start"
                        # รอโหลดเกมและกด Fast Start รัวๆ เป็นเวลา 12 วินาที
                        for _ in range(6):
                            if not self.running: break
                            controller.click_percent(*GAME_FAST_START)
                            time.sleep(2)
                            
                        self.status_msg = "Running in stage..."
                        self.run_start_time = time.time() # <-- เริ่มจับเวลาตรงนี้! (หลังโหลดเสร็จ)
                        
                        last_jump_time = time.time()
                        relay_used = False
                        game_over_timer = 0
                        
                        # ตัวแปรจับความเคลื่อนไหว
                        last_motion_thumb = None
                        static_frames = 0
                        
                        import random
                        self.box_pattern = random.choice(["RABBIT_JUMP", "SNAKE_SLIDE"]) if self.farm_mode == "BOX" else None
                        self.coin_pattern = random.choice(["AGILE_JUMPER", "SMART_SLIDER"]) if self.farm_mode == "COIN" else None
                        
                        while self.running:
                            img = vision.capture_screen()
                            
                            # [Hybrid Detection] ระบบที่ 2: Motion Detection (เช็คภาพจิ๋วมุมซ้ายบน)
                            # มุมซ้ายบน (X=10-30%, Y=20-40%) เป็นพื้นหลังที่จะเลื่อนตลอดเวลาตอนวิ่ง
                            # และจะนิ่งสนิท 100% ตอนหน้า Result (หลบอนิเมชั่นของกล่องสมบัติและตัวละคร)
                            w, h = img.size
                            thumb = list(img.crop((int(w*0.1), int(h*0.2), int(w*0.3), int(h*0.4))).resize((8, 8)).getdata())
                            if thumb == last_motion_thumb:
                                static_frames += 1
                            else:
                                static_frames = 0
                                last_motion_thumb = thumb
                                
                            # เช็คหน้าจบเกมก่อนเป็นอันดับแรก (เช็คทุกๆ 3 วินาที)
                            if game_over_timer % 30 == 0:
                                if vision.is_result_screen(img):
                                    self.status_msg = "Run completed. Result screen detected!"
                                    break
                                    
                            # ป้องกันเผลอกดปุ่มซื้อเพชร (หน้าต่างชุบชีวิต) หรือเผลอกดตอนเกมค้าง
                            if static_frames > 5:
                                self.status_msg = "Screen paused/popup detected. Halting actions..."
                                
                                # ถ้าค้างนานเกิน 8 วินาที แปลว่าอยู่หน้าจบเกมแน่นอน ให้ออกจากลูป
                                if static_frames > 80:
                                    self.status_msg = "Run completed. Result screen detected (Motion)!"
                                    break
                                    
                                game_over_timer += 1
                                time.sleep(0.1)
                                continue
                            
                            # ตรวจจับหน้าผลัดไม้ (ไม้ 1 ตาย)
                            if self.farm_mode == "COIN" and not relay_used and vision.is_relay_window(img, RELAY_SCAN_AREA):
                                self.status_msg = "Relaying to Cookie 2..."
                                controller.click_percent(*GAME_RELAY_COOKIE)
                                relay_used = True
                                time.sleep(2)
                                continue
                                
                            if self.farm_mode == "COIN":
                                # ระบบตาเลเซอร์สแกนสภาพแวดล้อม
                                env_state = vision.scan_environment(img)
                                
                                if env_state == "POTATO_SKILL":
                                    self.status_msg = "Potato Skill! Single Short Jump!"
                                    if time.time() - last_jump_time > 0.35:
                                        controller.click_percent(*GAME_JUMP_BTN)
                                        last_jump_time = time.time()
                                elif env_state == "HOLE":
                                    self.status_msg = "Hole detected! Double Jump!"
                                    controller.double_jump(GAME_JUMP_BTN)
                                    last_jump_time = time.time()
                                    time.sleep(0.1)
                                elif env_state == "OBSTACLE_LOW":
                                    self.status_msg = "Low Obstacle! Jump!"
                                    controller.click_percent(*GAME_JUMP_BTN)
                                    last_jump_time = time.time()
                                    time.sleep(0.1)
                                elif env_state == "OBSTACLE_HIGH":
                                    self.status_msg = "High Obstacle! Slide!"
                                    controller.click_percent(*GAME_SLIDE_BTN)
                                    time.sleep(0.2)
                                else:
                                    self.status_msg = f"Safe... ({self.coin_pattern})"
                                    if time.time() - last_jump_time > JUMP_INTERVAL:
                                        if self.coin_pattern == "AGILE_JUMPER":
                                            # AGILE_JUMPER: ชอบกระโดดคู่ (Double Jump) ตอนทางโล่งเพื่อเก็บเยลลี่ลอยฟ้า หรือกระโดดสั้นๆ ถี่ๆ
                                            if random.random() > 0.5:
                                                controller.double_jump(GAME_JUMP_BTN)
                                            else:
                                                controller.click_percent(*GAME_JUMP_BTN)
                                        else:
                                            # SMART_SLIDER: ชอบสไลด์ติดพื้นยาวๆ เพื่อความปลอดภัยสูงสุด (มุดหลบสิ่งกีดขวางที่อาจจะมองไม่เห็น)
                                            if random.random() > 0.2:
                                                controller.click_percent(*GAME_SLIDE_BTN)
                                                time.sleep(0.3) # สไลด์ค้างไว้นิดนึง
                                            else:
                                                controller.click_percent(*GAME_JUMP_BTN)
                                        last_jump_time = time.time()
                            else:
                                # BOX Mode: Anti-Macro Movements (สุ่มเดินแบบไม่ให้ซ้ำ)
                                if self.box_pattern == "RABBIT_JUMP":
                                    # RABBIT_JUMP: กระโดดถี่ๆ กระโดดคู่บ้าง แทบไม่สไลด์เลย
                                    if time.time() - last_jump_time > random.uniform(1.0, 3.0):
                                        self.status_msg = "Anti-Macro (RABBIT_JUMP): Jump!"
                                        if random.random() > 0.7:
                                            controller.double_jump(GAME_JUMP_BTN)
                                        else:
                                            controller.click_percent(*GAME_JUMP_BTN)
                                        last_jump_time = time.time()
                                else:
                                    # SNAKE_SLIDE: สไลด์ค้างติดพื้นยาวๆ นานๆทีกระโดดที
                                    if time.time() - last_jump_time > random.uniform(2.5, 5.0):
                                        if random.random() > 0.2:
                                            self.status_msg = "Anti-Macro (SNAKE_SLIDE): Slide!"
                                            controller.click_percent(*GAME_SLIDE_BTN)
                                            time.sleep(0.5) # สไลด์ค้าง
                                        else:
                                            self.status_msg = "Anti-Macro (SNAKE_SLIDE): Jump!"
                                            controller.click_percent(*GAME_JUMP_BTN)
                                        last_jump_time = time.time()
                                    
                            # เงื่อนไขออกจากลูป Gameplay ไปยัง Result
                            # บังคับจบเกมตามเวลาที่ตั้งค่าไว้ (Timer)
                            if self.use_timeout and hasattr(self, 'run_start_time') and self.run_start_time:
                                current_run_time = time.time() - self.run_start_time
                                current_timeout = self.coin_timeout if self.farm_mode == "COIN" else self.box_timeout
                                if current_run_time > current_timeout:
                                    self.status_msg = f"Time Limit Reached ({current_timeout}s). Forcing Result!"
                                    break
                            
                            # (ย้ายส่วนตรวจสอบ Result ไปไว้ด้านบนแล้ว)
                            
                            if static_frames > 80:  # ถ้านิ่งสนิทนาน 8 วินาที แปลว่าอยู่หน้าจบเกมแน่นอน
                                self.status_msg = "Run completed. Result screen detected (Motion)!"
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
                        
                    elif self.current_state == "LOBBY":
                        # ตรวจสอบอีกครั้งว่าอยู่หน้า Lobby จริงๆ ไหม (ป้องกันความผิดพลาด)
                        if vision.is_lobby_screen(img):
                            self.status_msg = "In Lobby. Navigating to Prep..."
                            time.sleep(1)
                            controller.click_percent(80.0, 85.0)
                            time.sleep(0.5)
                            controller.click_percent(80.0, 85.0) # กดย้ำอีกครั้งเผื่อเกมแลคหรือคลิกไม่ติด
                            time.sleep(4) # รอ 4 วินาทีให้หน้าจอเลื่อนไป Prep จนเสร็จสมบูรณ์
                            self.current_state = "PREP"
                            
                    elif self.current_state == "WAIT_FOR_LOBBY":
                        # ระบบนี้จะทำงานจนกว่าจะเห็นปุ่ม Play! สีเขียวในหน้า Lobby จริงๆ
                        if vision.is_lobby_screen(img):
                            self.status_msg = "Lobby detected! Waiting for UI animation..."
                            time.sleep(4) # รอ 4 วินาทีให้ปุ่ม Play สไลด์เข้ามาจนสุดและ UI นิ่งสนิท
                            self.current_state = "LOBBY"
                        elif vision.is_center_popup_button(img):
                            self.status_msg = "Popup/Box detected! Clicking..."
                            # กด 2 จุด: X=35 (เผื่อมีปุ่ม Open All โผล่มาฝั่งซ้าย) และ X=50 (ปุ่ม Confirm หรือ Open กล่องเดียวตรงกลาง)
                            controller.click_percent(35.0, 85.0)
                            time.sleep(1.5)
                            controller.click_percent(50.0, 85.0)
                            time.sleep(3.5)
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
