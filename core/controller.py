import win32gui
import win32con
import time
import random
from config import CLICK_OFFSET_PCT, CLICK_DELAY_MIN, CLICK_DELAY_MAX, TOUCH_HOLD_TIME

class Controller:
    def __init__(self, render_hwnd):
        self.render_hwnd = render_hwnd

    def _get_viewport_size(self):
        rect = win32gui.GetClientRect(self.render_hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        return width, height

    def _add_random_offset(self, val_pct):
        """ สุ่มเพิ่มหรือลดเปอร์เซ็นต์เล็กน้อยเพื่อไม่ให้จิ้มซ้ำจุดเดิมเป๊ะๆ """
        offset = random.uniform(-CLICK_OFFSET_PCT, CLICK_OFFSET_PCT)
        return max(0.0, min(100.0, val_pct + offset))

    def click_percent(self, x_pct, y_pct, randomize=True):
        """
        กดคลิกที่ตำแหน่ง x, y (เปอร์เซ็นต์) พร้อมระบบจำลองนิ้วคน (Anti-Ban)
        """
        width, height = self._get_viewport_size()

        if randomize:
            x_pct = self._add_random_offset(x_pct)
            y_pct = self._add_random_offset(y_pct)

        # แปลงเป็น Pixel จริง
        cx = int(width * x_pct / 100.0)
        cy = int(height * y_pct / 100.0)

        # สุ่มหน่วงเวลาก่อนกด
        time.sleep(random.uniform(CLICK_DELAY_MIN, CLICK_DELAY_MAX))

        # ส่งสัญญาณคลิกซ้าย
        lParam = (cy << 16) | cx
        win32gui.PostMessage(self.render_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        
        # หน่วงเวลาจำลองการกดนิ้วค้าง
        time.sleep(TOUCH_HOLD_TIME)
        
        win32gui.PostMessage(self.render_hwnd, win32con.WM_LBUTTONUP, 0, lParam)
        print(f"[*] Clicked at {x_pct:.1f}%, {y_pct:.1f}% -> ({cx}, {cy})")

    def double_jump(self, jump_pct_coord):
        """ คำสั่งกดกระโดด 2 จังหวะ (หลบเหว) """
        self.click_percent(*jump_pct_coord)
        time.sleep(0.1)  # หน่วงสั้นๆ ระหว่างจังหวะแรกและสอง
        self.click_percent(*jump_pct_coord)
        print("[*] Performed Double Jump!")
