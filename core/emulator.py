import win32gui

def get_emulator_window(window_title):
    """
    ค้นหา Window หลักของ Emulator ด้วยชื่อ Title (เช่น LDPlayer)
    """
    matched_hwnds = []
    def enum_windows_proc(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_title.lower() in title.lower():
                matched_hwnds.append(hwnd)
        return True

    win32gui.EnumWindows(enum_windows_proc, None)

    if not matched_hwnds:
        raise Exception(f"ไม่พบหน้าต่าง Emulator ที่มีชื่อ: {window_title}")
        
    # เลือก Window ที่มีขนาดใหญ่พอ (ป้องกันไปจับหน้าต่างซ่อน/Updater ของ LDPlayer)
    hwnd = matched_hwnds[0]
    for h in matched_hwnds:
        rect = win32gui.GetWindowRect(h)
        if rect[2] - rect[0] > 300 and rect[3] - rect[1] > 200:
            hwnd = h
            break
    # บังคับปรับขนาดหน้าต่าง Emulator ให้เป็นสัดส่วน 16:9 เสมอ (1280x750 เผื่อพื้นที่ Title Bar)
    # เพื่อแก้ปัญหาหน้าจอโดนตัด/แหว่ง เมื่อผู้ใช้ย่อหน้าต่างหรือตั้งค่าผิด
    try:
        rect = win32gui.GetWindowRect(hwnd)
        win32gui.MoveWindow(hwnd, rect[0], rect[1], 1280, 750, True)
    except Exception as e:
        print(f"Warning: Could not resize window: {e}")
        
    return hwnd

def get_render_window(main_hwnd, render_class, render_title):
    """
    ค้นหา Window ย่อย (Child Viewport) ที่ใช้สำหรับแสดงผลเกมจริงๆ
    โดยจะสแกนหา Child Window ที่มีขนาดพื้นที่ใหญ่ที่สุด (ซึ่งก็คือจอเกม)
    """
    child_hwnds = []
    def enum_child_proc(hwnd, lParam):
        lParam.append(hwnd)
        return True
    
    win32gui.EnumChildWindows(main_hwnd, enum_child_proc, child_hwnds)
    
    if not child_hwnds:
        raise Exception("ไม่พบหน้าต่างย่อย (Child Windows) ใน Emulator นี้เลย")
        
    largest_hwnd = None
    max_area = 0
    
    for hwnd in child_hwnds:
        if not win32gui.IsWindowVisible(hwnd):
            continue
        rect = win32gui.GetClientRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        area = width * height
        if area > max_area:
            max_area = area
            largest_hwnd = hwnd
            
    if largest_hwnd:
        return largest_hwnd
    else:
        raise Exception("ไม่พบ Render Window ที่มีขนาดใหญ่พอจะเป็นจอเกม")

def get_viewport_size(render_hwnd):
    """
    อ่านขนาดความกว้างและความสูงของ Viewport ในวินาทีปัจจุบัน
    รองรับกรณีที่ผู้ใช้ย่อ/ขยายหน้าต่างแบบ Real-time
    """
    rect = win32gui.GetClientRect(render_hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    return width, height
