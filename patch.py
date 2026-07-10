import codecs

with codecs.open('bot_engine.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('\r\n', '\n')

old_desync = """                    elif self.current_state == "GAMEPLAY":
                        # --- Global Desync Recovery ---
                        # หากบอทคิดว่ากำลังวิ่งอยู่ (GAMEPLAY) แต่ดันตรวจพบปุ่ม Play! ของหน้าหลัก
                        # แปลว่าเกิดการวืดกดไม่ติด หรือเกมเด้งกลับมาหน้าหลัก ให้ทำการรีเซ็ต State กลับไปเริ่มใหม่
                        if detected_state == "LOBBY":
                            self.status_msg = "Desync Detected! Force returning to LOBBY..."
                            global_static_frames = 0
                            self.current_state = "LOBBY"
                            time.sleep(2)
                            continue"""

new_desync = """                    elif self.current_state == "GAMEPLAY":
                        # --- Global Desync Recovery ---
                        if detected_state in ["LOBBY", "PREP"]:
                            self.status_msg = f"Desync Detected! Force returning to {detected_state}..."
                            global_static_frames = 0
                            self.current_state = detected_state
                            time.sleep(2)
                            continue"""

content = content.replace(old_desync, new_desync)

old_booster = """                        self.status_msg = f"Rolling Boosters ({self.farm_mode} Mode)..."
                        
                        # 1. กดกล่องสุ่ม
                        controller.click_percent(*PREP_RANDOM_BOOST)
                        time.sleep(1.5)
                        
                        # 2. กดปุ่ม Multi
                        controller.click_percent(*PREP_MULTI_TAB)
                        time.sleep(1)
                        
                        # 3. กด Multi-Buy ใน Popup
                        controller.click_percent(*PREP_MULTI_BUY)
                        
                        # 4. รอให้ระบบสุ่มอัตโนมัติ 30 วินาที
                        self.status_msg = "Waiting 30 seconds for Auto Multi-Buy..."
                        for _ in range(30):
                            if not self.running: break
                            time.sleep(1)
                        if not self.running: break"""

new_booster = """                        if time.time() - getattr(self, 'last_booster_roll_time', 0) > 60:
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
                            if not self.running: break"""

content = content.replace(old_booster, new_booster)

old_lobby_click = """                        # กดกึ่งกลางหน้าจอ 1 ครั้งเสมอเมื่อเข้า Lobby เพื่อปิด Level Up Popup หรือ Daily Login
                        controller.click_percent(50.0, 85.0)
                        time.sleep(1.0)"""

new_lobby_click = """                        # กดกึ่งกลางหน้าจอ 1 ครั้งเสมอเมื่อเข้า Lobby เพื่อปิด Level Up Popup หรือ Daily Login
                        controller.click_percent(50.0, 75.0)
                        time.sleep(0.5)
                        controller.click_percent(50.0, 85.0)
                        time.sleep(1.0)"""

content = content.replace(old_lobby_click, new_lobby_click)

content = content.replace('\n', '\r\n')

with codecs.open('bot_engine.py', 'w', 'utf-8') as f:
    f.write(content)

print("Patch successful!")
