import win32gui
import win32ui
import win32con
import numpy as np
import cv2
from PIL import Image
from config import BASE_WIDTH, BASE_HEIGHT


class Vision:
    def __init__(self, render_hwnd):
        self.render_hwnd = render_hwnd

    def capture_screen(self):
        rect = win32gui.GetClientRect(self.render_hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        hwndDC = win32gui.GetWindowDC(self.render_hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        import ctypes
        # Try flag 3 (PW_CLIENTONLY | PW_RENDERFULLCONTENT)
        result = ctypes.windll.user32.PrintWindow(self.render_hwnd, saveDC.GetSafeHdc(), 3)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # Fallback: หากภาพดำสนิทหรือ PrintWindow ล้มเหลว ให้ลองใช้ flag 0 (Default)
        if result != 1 or img.getbbox() is None:
            saveDC.SelectObject(saveBitMap)
            result = ctypes.windll.user32.PrintWindow(self.render_hwnd, saveDC.GetSafeHdc(), 0)
            if result == 1:
                bmpstr = saveBitMap.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.render_hwnd, hwndDC)

        # หากภาพยังคงดำสนิท ให้ใช้ท่าไม้ตาย ImageGrab (จับภาพสดจากหน้าจอ)
        if img.getbbox() is None:
            from PIL import ImageGrab
            try:
                left_top = win32gui.ClientToScreen(self.render_hwnd, (0, 0))
                right_bottom = win32gui.ClientToScreen(self.render_hwnd, (width, height))
                bbox = (left_top[0], left_top[1], right_bottom[0], right_bottom[1])
                img = ImageGrab.grab(bbox).convert('RGB')
            except Exception as e:
                print(f"ImageGrab fallback failed: {e}")

        if img.getbbox() is None:
            raise Exception("Failed to capture screen (Image is black even with ImageGrab).")

        return img

    def get_color_at_percent(self, img, x_pct, y_pct):
        width, height = img.size
        cx = int(width * x_pct / 100.0)
        cy = int(height * y_pct / 100.0)
        cx = max(0, min(cx, width - 1))
        cy = max(0, min(cy, height - 1))
        return img.getpixel((cx, cy))

    def scan_environment(self, img):
        import config
        width, height = img.size
        
        start_x = int(width * config.SCAN_X_START / 100.0)
        end_x = int(width * config.SCAN_X_END / 100.0)
        start_x, end_x = max(0, min(start_x, width-1)), max(0, min(end_x, width-1))
        if start_x > end_x: start_x, end_x = end_x, start_x
        
        y_head = max(0, min(int(height * config.SCAN_HEAD_Y / 100.0), height-1))
        y_waist = max(0, min(int(height * config.SCAN_WAIST_Y / 100.0), height-1))
        y_ground = max(0, min(int(height * config.SCAN_GROUND_Y / 100.0), height-1))
        y_potato = max(0, min(int(height * config.SCAN_POTATO_Y / 100.0), height-1))
        
        black_cnt = 0
        potato_cnt = 0
        obs_head_cnt = 0
        obs_waist_cnt = 0
        
        state = "SAFE"
        
        for x in range(start_x, end_x + 1):
            # 1. เช็คพื้นล่างสุด (หลุมดำ)
            r, g, b = img.getpixel((x, y_ground))
            if r < 30 and g < 30 and b < 30:
                black_cnt += 1
            else:
                black_cnt = 0
                
            # 1.5 เช็คระดับพื้น (ก้อนมันฝรั่ง และ มายองเนส)
            pr, pg, pb = img.getpixel((x, y_potato))
            is_potato = (config.POTATO_R_MIN <= pr <= config.POTATO_R_MAX and 
                         config.POTATO_G_MIN <= pg <= config.POTATO_G_MAX and 
                         config.POTATO_B_MIN <= pb <= config.POTATO_B_MAX)
            is_mayo = (config.MAYO_R_MIN <= pr <= config.MAYO_R_MAX and 
                       config.MAYO_G_MIN <= pg <= config.MAYO_G_MAX and 
                       config.MAYO_B_MIN <= pb <= config.MAYO_B_MAX)
            
            if is_potato or is_mayo:
                potato_cnt += 1
                
            # 2. เช็คระดับหัว (หาสิ่งกีดขวางสีทึบ)
            hr, hg, hb = img.getpixel((x, y_head))
            if hr < 80 and hg < 80 and hb < 80:
                obs_head_cnt += 1
            else:
                obs_head_cnt = 0
                
            # 3. เช็คระดับเอว
            wr, wg, wb = img.getpixel((x, y_waist))
            if wr < 80 and wg < 80 and wb < 80:
                obs_waist_cnt += 1
            else:
                obs_waist_cnt = 0
                
            # ประเมินผลแบบ Real-time ทีละจุด
            if potato_cnt >= config.POTATO_THRESHOLD:
                return "POTATO_SKILL" # สำคัญสุด ให้กวาดเหรียญ
            if black_cnt >= config.HOLE_WIDTH_THRESHOLD:
                return "HOLE"
            if obs_head_cnt >= config.OBSTACLE_THRESHOLD:
                state = "OBSTACLE_HIGH"
            if obs_waist_cnt >= config.OBSTACLE_THRESHOLD:
                return "OBSTACLE_LOW" # ถ้ามีอันตรายข้างล่าง ต้องโดด สำคัญกว่าสไลด์
                
        return state

    def ocr_read_text(self, img, rect_pct=None, only_digits=False):
        try:
            import pytesseract
            import os
            import cv2
            import numpy as np
            from config import TESSERACT_CMD
            
            if not os.path.exists(TESSERACT_CMD):
                return ""
                
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
            
            if rect_pct:
                w, h = img.size
                x = int(rect_pct[0] * w / 100.0)
                y = int(rect_pct[1] * h / 100.0)
                rw = int(rect_pct[2] * w / 100.0)
                rh = int(rect_pct[3] * h / 100.0)
                img = img.crop((x, y, x + rw, y + rh))
                
            open_cv_image = np.array(img)
            if len(open_cv_image.shape) == 3:
                gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
            else:
                gray = open_cv_image
                
            # เพิ่มขนาดภาพ 2 เท่าช่วยให้ OCR อ่านง่ายขึ้น
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            # ใช้ Otsu threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            custom_config = '--psm 7'
            if only_digits:
                # อนุญาตให้มีลูกน้ำและจุดด้วย เพื่อกัน Tesseract พยายามบีบให้ลูกน้ำเป็นตัวเลข
                custom_config += ' -c tessedit_char_whitelist=0123456789,.'
                
            text = pytesseract.image_to_string(thresh, config=custom_config)
            return text.strip()
        except Exception as e:
            print(f"[OCR Error] {e}")
            return ""

    def read_coins_result(self, img):
        # บีบกรอบ Y ให้แคบลง (Y=53% ถึง 60%) เพื่อไม่ให้ไปกวาดโดนบรรทัด XP ที่อยู่ด้านล่าง
        text = self.ocr_read_text(img, rect_pct=(65.0, 53.0, 25.0, 7.0), only_digits=True)
        # เผื่อหลุดมา 2 บรรทัด ให้เอาแค่บรรทัดแรก (บรรทัดเหรียญ)
        text = text.split('\n')[0]
        nums = ''.join(filter(str.isdigit, text))
        if nums:
            return int(nums)
        return 0

    def extract_obstacle_features(self, img):
        """Extract multi-scale features from ROI for AI learning."""
        width, height = img.size
        
        # Crop ROI: X=15% to 45%, Y=40% to 90% (directly in front of Cookie)
        x1 = int(width * 0.15)
        x2 = int(width * 0.45)
        y1 = int(height * 0.40)
        y2 = int(height * 0.90)
        
        roi = img.crop((x1, y1, x2, y2))
        roi_np = np.array(roi)
        
        # Convert to grayscale
        gray = cv2.cvtColor(roi_np, cv2.COLOR_RGB2GRAY)
        
        # 1. Level 1: Direct Pixel (20x20)
        resized_gray = cv2.resize(gray, (20, 20))
        pixel_features = resized_gray.flatten().astype(np.float32) / 255.0  # Normalize to [0, 1]
        
        # 2. Level 2: HOG (Edge Detection)
        # Resize to standard size for HOG (e.g. 32x64)
        hog_img = cv2.resize(gray, (32, 64))
        
        # Initialize HOG descriptor with small cell/block sizes
        winSize = (32, 64)
        blockSize = (16, 16)
        blockStride = (8, 8)
        cellSize = (8, 8)
        nbins = 9
        
        # Create HOG descriptor
        hog = cv2.HOGDescriptor(winSize, blockSize, blockStride, cellSize, nbins)
        hog_features = hog.compute(hog_img).flatten()
        
        # Normalize HOG features (they are usually already normalized per block, but just to be safe)
        if np.max(hog_features) > 0:
            hog_features = hog_features / np.max(hog_features)
            
        # Combine both vectors
        combined_features = np.concatenate((pixel_features, hog_features))
        
        return combined_features

    def has_get_sign(self, img, rect_pct):
        # เลิกใช้ OCR
        return False

    def is_relay_window(self, img, rect_pct):
        # Scan a box around the center where the green Relay button background is expected.
        width, height = img.size
        x1 = int(width * (rect_pct[0] / 100))
        y1 = int(height * (rect_pct[1] / 100))
        x2 = int(width * (rect_pct[2] / 100))
        y2 = int(height * (rect_pct[3] / 100))
        
        green_count = 0
        total_pixels = 0
        
        for y in range(y1, y2, 5): # Check every 5th pixel for speed
            for x in range(x1, x2, 5):
                r, g, b = img.getpixel((x, y))
                # ปุ่มไม้ผลัดจะเป็นสีเขียวสว่าง (Lime green)
                if g > 150 and r < g - 30 and b < g - 30:
                    green_count += 1
                total_pixels += 1
                
        # If at least 15% of the sampled pixels are green, consider it the relay button
        return total_pixels > 0 and (green_count / total_pixels) > 0.15

    def is_revive_window(self, img, rect_pct):
        # เลิกใช้ OCR
        return False
        
    def is_result_screen(self, img, rect_pct=None):
        # 1. Fast Check: สแกนเพื่อหาปุ่ม OK (สีเขียว) และ Show Off (สีฟ้า)
        width, height = img.size
        
        green_cnt = 0
        blue_cnt = 0
        
        # สแกนปุ่ม OK (X = 30-50%) และ Show Off (X = 55-75%)
        # สแกนหลายระดับความสูง (Y = 82%, 85%, 88%, 91%) ป้องกันพลาด!
        for y_pct in [0.82, 0.85, 0.88, 0.91]:
            y = int(height * y_pct)
            
            # Check Green (OK)
            for x in range(int(width * 0.30), int(width * 0.50), 2): 
                r, g, b = img.getpixel((x, y))
                if g > 150 and r < g - 20 and b < g - 20:
                    green_cnt += 1
                    
            # Check Blue (Show Off)
            for x in range(int(width * 0.55), int(width * 0.75), 2):
                r, g, b = img.getpixel((x, y))
                if b > 140 and g > 100 and r < 120:
                    blue_cnt += 1
                    
        # ต้องเจอทั้ง 2 ปุ่ม ถึงจะมั่นใจ 100% ว่าไม่ใช่แสงออร่าตอนวิ่ง
        if green_cnt > 50 and blue_cnt > 50:
            return True
                
    def is_multi_button_popup(self, img):
        # สแกนหาปุ่ม Multi สีชมพู ภายใน Popup (X=84-89%, Y=29-31%)
        width, height = img.size
        pink_cnt = 0
        
        for y_pct in [0.29, 0.30, 0.31]:
            y = int(height * y_pct)
            for x in range(int(width * 0.84), int(width * 0.89), 1):
                r, g, b = img.getpixel((x, y))
                # สีชมพู/แดงสว่าง: R โดดเด่นกว่า G ชัดเจน
                if r > 150 and r > g + 40:
                    pink_cnt += 1
                    
        return pink_cnt > 10

    def is_prep_screen(self, img):
        # ต้องมีปุ่ม Play สีเขียว
        if not self.is_lobby_screen(img):
            return False
            
        # สแกนหากล่องสุ่ม Booster สีทอง/เหลือง (X=42-45%, Y=81-83%)
        width, height = img.size
        gold_cnt = 0
        for y_pct in [0.81, 0.82, 0.83]:
            y = int(height * y_pct)
            for x_pct in [0.42, 0.43, 0.44]:
                x = int(width * x_pct)
                r, g, b = img.getpixel((x, y))
                # สีทอง/เหลือง: R และ G สูง, B ต่ำ
                if r > 150 and g > 100 and b < 100 and r > g:
                    gold_cnt += 1
        
        # ถ้ามีสีทองตรงกล่องสุ่ม แปลว่าเป็นหน้า Prep (ถ้าเป็น Lobby จะเป็นกรอบเพื่อนสีทึบ)
        return gold_cnt > 3
        
    def determine_state(self, img):
        if self.is_result_screen(img):
            return "RESULTS"
        if self.is_prep_screen(img):
            return "PREP"
        if self.is_lobby_screen(img):
            return "LOBBY"
        return "GAMEPLAY"

    def is_lobby_screen(self, img):
        # สแกนหาปุ่ม Play! สีเขียวที่มุมขวาล่าง
        width, height = img.size
        green_cnt = 0
        
        # เช็คปุ่ม Play! สีเขียว (ช่วง X = 65% ถึง 85%)
        for y_pct in [0.85, 0.88, 0.91]:
            y = int(height * y_pct)
            for x in range(int(width * 0.65), int(width * 0.85), 2):
                r, g, b = img.getpixel((x, y))
                # สีเขียวเด่นชัด (หลบแสงหลอก)
                if g > 110 and g > r + 10 and g > b + 10:
                    green_cnt += 1
                    
        # ต้องเจอปุ่ม Play สีเขียวขนาดใหญ่เท่านั้น (ป้องกันไปสับสนกับไอเทมสีเขียวชิ้นเล็กๆ ในหน้าต่างเพื่อน)
        return green_cnt > 150

    def is_center_popup_button(self, img):
        # สแกนหาปุ่ม (ฟ้าอ่อน หรือ เขียว) ช่วงล่างของจอ (X=25-75%)
        # ครอบคลุมทั้งปุ่มตรงกลาง (Open/Confirm) และปุ่มฝั่งซ้าย (Open All)
        width, height = img.size
        
        blue_cnt = 0
        green_cnt = 0
        
        for y_pct in [0.82, 0.85, 0.88, 0.91]:
            y = int(height * y_pct)
            
            # Check Light Blue (X=25-75% ครอบคลุมปุ่ม Open All และ Confirm)
            for x in range(int(width * 0.25), int(width * 0.75), 2):
                r, g, b = img.getpixel((x, y))
                if b > 140 and b > r + 20 and g > r + 10:
                    blue_cnt += 1
                    
            # Check Green (สแกนแค่ X=35-45% เพื่อหลบซองจดหมายหัวใจเพื่อนที่ X=48-55%)
            for x in range(int(width * 0.35), int(width * 0.45), 2):
                r, g, b = img.getpixel((x, y))
                if g > 130 and g > r + 10 and g > b + 10:
                    green_cnt += 1
                    
        # เจอปุ่มใดปุ่มหนึ่งในตำแหน่งที่กำหนด ถือว่าเป็น Popup Box/Level Up
        if blue_cnt > 40 or green_cnt > 40:
            return True
            
        return False

