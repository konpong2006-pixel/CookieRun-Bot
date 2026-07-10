import codecs

with codecs.open('bot_engine.py', 'r', 'utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'self.status_msg = f"Rolling Boosters' in line:
        start_idx = i
    if '# 5. ปิด Popup กล่องสุ่ม' in line:
        end_idx = i + 2  # include time.sleep(2)

if start_idx != -1 and end_idx != -1:
    booster_lines = [
        '                        # ปิด Popup ที่อาจจะค้างอยู่ก่อน\n',
        '                        controller.click_percent(90.0, 10.0)\n',
        '                        time.sleep(1)\n',
        '                        if time.time() - getattr(self, "last_booster_roll_time", 0) > 60:\n',
        '                            self.status_msg = f"Rolling Boosters ({self.farm_mode} Mode)..."\n',
        '                            controller.click_percent(*PREP_RANDOM_BOOST)\n',
        '                            time.sleep(1.5)\n',
        '                            controller.click_percent(*PREP_MULTI_TAB)\n',
        '                            time.sleep(1)\n',
        '                            controller.click_percent(*PREP_MULTI_BUY)\n',
        '                            self.status_msg = "Waiting 15 seconds for Auto Multi-Buy..."\n',
        '                            for _ in range(15):\n',
        '                                if not self.running: break\n',
        '                                time.sleep(1)\n',
        '                            self.last_booster_roll_time = time.time()\n',
        '                            if not self.running: break\n',
        '                        # ปิด Popup กล่องสุ่ม (กดซ้ำเพื่อความชัวร์)\n',
        '                        controller.click_percent(90.0, 10.0)\n',
        '                        time.sleep(1.5)\n',
        '                        controller.click_percent(90.0, 10.0)\n',
        '                        time.sleep(1.5)\n'
    ]
    new_lines = lines[:start_idx] + booster_lines + lines[end_idx+1:]
    with codecs.open('bot_engine.py', 'w', 'utf-8') as f:
        f.writelines(new_lines)
    print("Replaced by index!")
else:
    print(f"Indices not found! start: {start_idx}, end: {end_idx}")
