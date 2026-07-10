$content = Get-Content -Raw -Encoding UTF8 bot_engine.py

$old_desync = @"
                    elif self.current_state == `"GAMEPLAY`":
                        # --- Global Desync Recovery ---
                        # หากบอทคิดว่ากำลังวิ่งอยู่ (GAMEPLAY) แต่ดันตรวจพบปุ่ม Play! ของหน้าหลัก
                        # แปลว่าเกิดการวืดกดไม่ติด หรือเกมเด้งกลับมาหน้าหลัก ให้ทำการรีเซ็ต State กลับไปเริ่มใหม่
                        if detected_state == `"LOBBY`":
"@

$new_desync = @"
                    elif self.current_state == `"GAMEPLAY`":
                        # --- Global Desync Recovery ---
                        # หากบอทคิดว่ากำลังวิ่งอยู่ (GAMEPLAY) แต่ดันตรวจพบปุ่ม Play! ของหน้าหลัก
                        # หรือไปอยู่ในหน้าเตรียมตัว (PREP) ให้ทำการรีเซ็ต State กลับไปเริ่มใหม่
                        if detected_state in [`"LOBBY`", `"PREP`"]:
"@

$old_booster = @"
                        self.status_msg = f`"Rolling Boosters ({self.farm_mode} Mode)...`"
                        
                        # 1. กดกล่องสุ่ม
                        controller.click_percent(*PREP_RANDOM_BOOST)
                        time.sleep(1.5)
                        
                        # 2. กดปุ่ม Multi
                        controller.click_percent(*PREP_MULTI_TAB)
                        time.sleep(1)
                        
                        # 3. กด Multi-Buy ใน Popup
                        controller.click_percent(*PREP_MULTI_BUY)
                        
                        # 4. รอให้ระบบสุ่มอัตโนมัติ 30 วินาที
                        self.status_msg = `"Waiting 30 seconds for Auto Multi-Buy...`"
                        for _ in range(30):
                            if not self.running: break
                            time.sleep(1)
                        if not self.running: break
                        
                        # 5. ปิด Popup กล่องสุ่ม (กดตรงไหนก็ได้ที่ว่างๆ หรือ X=90 Y=10)
                        controller.click_percent(90.0, 10.0)
                        time.sleep(2)
"@

$new_booster = @"
                        # ปิด Popup ที่อาจจะค้างอยู่ก่อน
                        controller.click_percent(90.0, 10.0)
                        time.sleep(1)

                        if time.time() - getattr(self, `"last_booster_roll_time`", 0) > 60:
                            self.status_msg = f`"Rolling Boosters ({self.farm_mode} Mode)...`"
                            
                            # 1. กดกล่องสุ่ม
                            controller.click_percent(*PREP_RANDOM_BOOST)
                            time.sleep(1.5)
                            
                            # 2. กดปุ่ม Multi
                            controller.click_percent(*PREP_MULTI_TAB)
                            time.sleep(1)
                            
                            # 3. กด Multi-Buy ใน Popup
                            controller.click_percent(*PREP_MULTI_BUY)
                            
                            # 4. รอให้ระบบสุ่มอัตโนมัติ 15 วินาที
                            self.status_msg = `"Waiting 15 seconds for Auto Multi-Buy...`"
                            for _ in range(15):
                                if not self.running: break
                                time.sleep(1)
                            
                            self.last_booster_roll_time = time.time()
                            if not self.running: break
                        
                        # 5. ปิด Popup กล่องสุ่ม (กดซ้ำเพื่อความชัวร์)
                        controller.click_percent(90.0, 10.0)
                        time.sleep(1.5)
                        controller.click_percent(90.0, 10.0)
                        time.sleep(1.5)
"@

# Fix carriage returns for matching
$old_desync = $old_desync -replace "`r`n", "`n"
$new_desync = $new_desync -replace "`r`n", "`n"
$old_booster = $old_booster -replace "`r`n", "`n"
$new_booster = $new_booster -replace "`r`n", "`n"
$content = $content -replace "`r`n", "`n"

if ($content.Contains($old_desync)) {
    Write-Host "Found desync logic"
    $content = $content.Replace($old_desync, $new_desync)
} else {
    Write-Host "Desync logic NOT found"
}

if ($content.Contains($old_booster)) {
    Write-Host "Found booster logic"
    $content = $content.Replace($old_booster, $new_booster)
} else {
    Write-Host "Booster logic NOT found"
}

$content = $content -replace "`n", "`r`n"
Set-Content -Path bot_engine.py -Value $content -Encoding UTF8
