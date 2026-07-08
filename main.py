import time
import sys
from config import *
from core.emulator import get_emulator_window, get_render_window
from core.controller import Controller
from core.vision import Vision

def main():
    print("=" * 40)
    print("🤖 Cookie Run Auto Farm Bot Started!")
    print("=" * 40)

    try:
        print(f"[*] Searching for {EMULATOR_WINDOW_TITLE}...")
        main_hwnd = get_emulator_window(EMULATOR_WINDOW_TITLE)
        render_hwnd = get_render_window(main_hwnd, EMULATOR_RENDER_CLASS, EMULATOR_RENDER_TITLE)
        print("[+] Found Emulator Viewport!")

        controller = Controller(render_hwnd)
        vision = Vision(render_hwnd)

        current_state = "LOBBY"
        
        while True:
            try:
                img = vision.capture_screen()
                
                if current_state == "LOBBY":
                    print("[State: LOBBY] Checking status...")
                    
                    # ตรวจสอบป้าย Get ของโบราณวัตถุ
                    if vision.has_get_sign(img, LOBBY_RELIC_GET_AREA):
                        print("[+] Found 'Get' sign. Claiming relic...")
                        controller.click_percent(*LOBBY_RELIC_CLAIM)
                        time.sleep(2)
                        controller.click_percent(*LOBBY_RELIC_CLOSE)
                        time.sleep(1)
                    
                    print("[*] Pressing Play...")
                    controller.click_percent(*LOBBY_PLAY_BTN)
                    time.sleep(3)
                    current_state = "PREP"

                elif current_state == "PREP":
                    print("[State: PREP] Rolling Boosters...")
                    
                    # 1. กดกล่องสุ่ม
                    controller.click_percent(*PREP_RANDOM_BOOST)
                    time.sleep(1)
                    
                    # 2. กดปุ่ม Multi
                    controller.click_percent(*PREP_MULTI_TAB)
                    time.sleep(1)
                    
                    # 3. กด Multi-Buy ใน Popup
                    controller.click_percent(*PREP_MULTI_BUY)
                    
                    # 4. รอให้ระบบสุ่มอัตโนมัติ 20 วินาที
                    print("[*] Waiting 20 seconds for Auto Multi-Buy...")
                    time.sleep(20)
                    
                    # 5. กด Stop เผื่อสุ่มไม่เจอ (ถ้าเจอแล้ว ปุ่มนี้คือ Play! จะเป็นการเริ่มเกมเลย)
                    print("[*] Pressing Stop/Play...")
                    controller.click_percent(*PREP_START_GAME)
                    time.sleep(2)
                    
                    # 6. กด Play! ซ้ำอีกรอบเพื่อความชัวร์ (เผื่อเมื่อกี้เป็นการกด Stop)
                    controller.click_percent(*PREP_START_GAME)
                    time.sleep(5)
                    
                    controller.click_percent(*GAME_FAST_START)
                    print("[*] Fast start triggered.")
                    current_state = "GAMEPLAY"

                elif current_state == "GAMEPLAY":
                    print("[State: GAMEPLAY] Running...")
                    
                    last_jump_time = time.time()
                    relay_used = False
                    game_over_timer = 0
                    
                    while True:
                        img = vision.capture_screen()
                        
                        # ตรวจจับหน้าผลัดไม้ (ไม้ 1 ตาย)
                        if not relay_used and vision.is_relay_window(img, RELAY_SCAN_AREA):
                            print("[!] Cookie 1 down. Relaying to Cookie 2 (Ninja)...")
                            controller.click_percent(*GAME_RELAY_COOKIE)
                            relay_used = True
                            time.sleep(2) # รออนิเมชั่นลงพื้น
                            continue
                            
                        # เช็คหลุมดำ
                        if vision.is_hole_detected(img, *HOLE_SCAN_POINT):
                            controller.double_jump(GAME_JUMP_BTN)
                            last_jump_time = time.time()
                        else:
                            # กระโดดทีละ 1 สเต็ป ตามเวลา (0.8s)
                            if time.time() - last_jump_time > JUMP_INTERVAL:
                                controller.click_percent(*GAME_JUMP_BTN)
                                last_jump_time = time.time()
                                
                        # เงื่อนไขออกจากลูป Gameplay ไปยัง Result
                        # ถ้ารูปแบบหน้าจอมีการเปลี่ยนเป็นหน้า Result (สแกนหาปุ่มเปิดกล่อง หรือ ป้ายคะแนน)
                        # สมมติเช็คจากสีปุ่ม OK หรือมีเวลาเกินที่กำหนด
                        # ตัวอย่าง: ใช้เวลาเป็นตัวตัดจบชั่วคราว (เกมปกติตานึงประมาณ 90 วิ)
                        game_over_timer += 0.1
                        if game_over_timer > 90.0:
                            print("[*] Run completed.")
                            break
                            
                        time.sleep(0.1)
                        
                    time.sleep(5)
                    current_state = "RESULTS"

                elif current_state == "RESULTS":
                    print("[State: RESULTS] Processing results...")
                    
                    # เช็คหน้าชุบชีวิตเพชรฟ้า
                    img = vision.capture_screen()
                    if vision.is_revive_window(img, RESULT_REVIVE_SCAN_AREA):
                        print("[!] Revive window detected. Waiting 15s to timeout (save crystals).")
                        time.sleep(15)
                        print("[*] Timeout finished.")
                    else:
                        time.sleep(5) # รอเวลาปกติ
                    
                    controller.click_percent(*RESULT_OPEN_ALL)
                    time.sleep(2)
                    
                    controller.click_percent(*RESULT_CONFIRM)
                    time.sleep(4)
                    
                    print("[+] Cycle Complete! Returning to Lobby...")
                    current_state = "LOBBY"

            except Exception as e:
                print(f"[Error in State Machine]: {e}")
                time.sleep(3)

    except Exception as ex:
        print(f"Fatal Error: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    main()
