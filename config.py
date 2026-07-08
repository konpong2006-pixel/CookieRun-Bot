import os

# ==========================================
# ⚙️ SYSTEM SETTINGS
# ==========================================
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# สำหรับ MuMu Player ให้ใช้ค่าด้านล่างนี้ (หากหาไม่เจอ ลองเปลี่ยนชื่อเป็น MuMu Player X หรือเวอร์ชันที่คุณใช้)
EMULATOR_WINDOW_TITLE = "Android Device"
EMULATOR_RENDER_CLASS = "subWin"
EMULATOR_RENDER_TITLE = "sub"

BASE_WIDTH = 1280
BASE_HEIGHT = 720

# ==========================================
# 📍 COORDINATES & SCAN AREAS (Percentage 0.0 - 100.0)
# ==========================================
# 1. Lobby
LOBBY_PLAY_BTN = (82.0, 85.0)
LOBBY_RELIC_CLAIM = (45.0, 15.0)
LOBBY_RELIC_GET_AREA = (40.0, 8.0, 50.0, 20.0) # พื้นที่สแกนคำว่า Get
LOBBY_RELIC_CLOSE = (90.0, 10.0) # ปุ่มปิดหน้าต่าง Relic สมมติขวาบน

# 2. Prep Screen
PREP_RANDOM_BOOST = (43.0, 82.0)    # กล่องสุ่ม Mystery Box (แถว 2 คอลัมน์ 3)
PREP_MULTI_TAB = (86.0, 30.0)       # ปุ่ม Multi สีชมพูขวามือ
PREP_MULTI_BUY = (50.0, 82.0)       # ปุ่ม Multi-Buy สีเขียวใน Popup
PREP_START_GAME = (82.0, 85.0)
PREP_BOOST_TEXT_AREA = (30.0, 40.0, 70.0, 60.0)

# 3. Gameplay Screen
GAME_JUMP_BTN = (15.0, 85.0)
GAME_SLIDE_BTN = (85.0, 85.0)
GAME_FAST_START = (85.0, 85.0)
GAME_RELAY_COOKIE = (50.0, 60.0)

# ระบบตาเลเซอร์ 3 ระดับ (Laser Eye System)
SCAN_X_START = 20.0        # จุดเริ่มสแกนแกน X
SCAN_X_END = 80.0          # จุดสิ้นสุดสแกนแกน X (กวาดให้กว้างขึ้นถึง 80%)
SCAN_HEAD_Y = 55.0         # สแกนหาสิ่งกีดขวางระดับหัว (สไลด์)
SCAN_WAIST_Y = 70.0        # สแกนหาสิ่งกีดขวางระดับเอว (กระโดด)
SCAN_GROUND_Y = 92.0       # สแกนหาหลุมดำที่พื้นล่างสุด
SCAN_POTATO_Y = 80.0       # สแกนหาก้อนมันฝรั่ง/มายองเนสที่วางอยู่บนพื้น

# ตั้งค่าเกณฑ์ความกว้าง
HOLE_WIDTH_THRESHOLD = 40  # หลุมดำต้องกว้างอย่างน้อย 40 พิกเซล
OBSTACLE_THRESHOLD = 15    # สิ่งกีดขวางต้องกว้างอย่างน้อย 15 พิกเซล
POTATO_THRESHOLD = 20      # ก้อนมันฝรั่งกว้างอย่างน้อย 20 พิกเซล

# ตั้งค่าสีก้อนมันฝรั่ง (สีทอง/เหลืองเข้ม)
POTATO_R_MIN, POTATO_R_MAX = 200, 255
POTATO_G_MIN, POTATO_G_MAX = 150, 230
POTATO_B_MIN, POTATO_B_MAX = 0, 100

# ตั้งค่าสีมายองเนส (สีขาวสว่าง)
MAYO_R_MIN, MAYO_R_MAX = 240, 255
MAYO_G_MIN, MAYO_G_MAX = 240, 255
MAYO_B_MIN, MAYO_B_MAX = 240, 255

RELAY_SCAN_AREA = (40.0, 40.0, 60.0, 50.0) # พื้นที่สแกนหน้าเปลี่ยนไม้

# 4. Results
RESULT_OPEN_ALL = (50.0, 85.0)     # ตำแหน่งปุ่ม Open All ตรงกลางจอด้านล่าง
RESULT_CONFIRM = (40.0, 85.0)      # ตำแหน่งปุ่ม OK (สีเขียวซ้ายมือ)
RESULT_REVIVE_SCAN_AREA = (30.0, 70.0, 70.0, 90.0) # ตรวจหาหน้าชุบชีวิต

# ==========================================
# ⏱️ TIMINGS & DELAYS
# ==========================================
CLICK_OFFSET_PCT = 2.0
CLICK_DELAY_MIN = 0.05
CLICK_DELAY_MAX = 0.15
TOUCH_HOLD_TIME = 0.05
JUMP_INTERVAL = 0.8 # กระโดดทุก 0.8 วิ
