import cv2
import numpy as np
from core.emulator import get_emulator_window, get_render_window
from core.vision import Vision
import config

def main():
    print("Capturing screen for debugging...")
    try:
        main_hwnd = get_emulator_window(config.EMULATOR_WINDOW_TITLE)
        render_hwnd = get_render_window(main_hwnd, config.EMULATOR_RENDER_CLASS, config.EMULATOR_RENDER_TITLE)
    except Exception as e:
        print(f"Error finding emulator: {e}")
        return

    vision = Vision(render_hwnd)
    img_pil = vision.capture_screen()
    
    # แปลงภาพจาก PIL เป็น OpenCV (BGR)
    img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    height, width = img.shape[:2]

    points_to_draw = [
        (config.PREP_RANDOM_BOOST, "Random Box", (255, 0, 0)),    # น้ำเงิน
        (config.PREP_MULTI_TAB, "Multi Tab", (0, 0, 255)),        # แดง
        (config.PREP_MULTI_BUY, "Multi Buy", (0, 255, 0)),        # เขียว
        (config.PREP_START_GAME, "Start/Stop", (0, 255, 255))     # เหลือง
    ]

    for pct_pos, name, color in points_to_draw:
        x_pct, y_pct = pct_pos
        cx = int(width * x_pct / 100.0)
        cy = int(height * y_pct / 100.0)
        
        # วาดวงกลมและข้อความ
        cv2.circle(img, (cx, cy), 15, color, -1)
        cv2.putText(img, name, (cx - 20, cy - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    save_path = "debug_click.png"
    cv2.imwrite(save_path, img)
    print(f"Debug image saved to {save_path}!")
    
    # พยายามเปิดรูปให้ดูทันที
    import os
    os.startfile(save_path)

if __name__ == "__main__":
    main()
