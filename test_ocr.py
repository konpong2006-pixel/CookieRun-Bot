import time
import win32gui
import cv2
import numpy as np
import pytesseract
import sys
import os
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import TESSERACT_CMD
from core.emulator import get_emulator_window, get_render_window
from core.vision import Vision

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def main():
    print("Please open the Result screen in MuMu Player.")
    print("Waiting 5 seconds...")
    time.sleep(5)
    
    try:
        main_hwnd = get_emulator_window("Android Device")
        render_hwnd = get_render_window(main_hwnd, "subWin", "sub")
        vision = Vision(render_hwnd)
        
        img = vision.capture_screen()
        width, height = img.size
        print(f"Captured screen size: {width}x{height}")
        
        crop_rect = (int(width*0.75), int(height*0.52), int(width*0.95), int(height*0.62))
        coin_img = img.crop(crop_rect)
        coin_img.save("test_coin_raw.jpg")
        print("Saved raw crop to test_coin_raw.jpg")
        
        gray = cv2.cvtColor(np.array(coin_img), cv2.COLOR_RGB2GRAY)
        
        # Test THRESH_BINARY
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        cv2.imwrite("test_coin_thresh.jpg", thresh)
        print("Saved thresholded image to test_coin_thresh.jpg")
        
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789,'
        text = pytesseract.image_to_string(thresh, config=custom_config)
        print(f"OCR Result: '{text.strip()}'")
        
        clean_number = "".join(filter(str.isdigit, text))
        print(f"Cleaned Number: '{clean_number}'")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
