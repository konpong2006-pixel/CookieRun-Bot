# Cookie Run Auto Farm Bot (Stage 1) 🍪🪙

บอทสำหรับฟาร์มเหรียญในด่าน 1 อัตโนมัติ พร้อมระบบป้องกันการแบน (Anti-Ban) 
ออกแบบมารองรับ Emulator ยอดนิยมเช่น LDPlayer และ MuMu Player โดยสามารถย่อ/ขยายขนาดหน้าจอได้อย่างอิสระ!

## 🌟 ฟีเจอร์หลัก (Features)
- **Dynamic Resizing**: รองรับการย่อ/ขยายจอ Emulator โดยพิกัดการกดคลิกไม่เพี้ยน (อิงจากระบบ % + ค้นหา Viewport อัตโนมัติ)
- **Lanczos Upscaling OCR**: อ่านตัวหนังสือได้แม่นยำ 100% ด้วยการขยายภาพให้คมชัดก่อนส่งให้ Tesseract OCR แม้จะย่อจอจนเล็กสุดๆ
- **Human-Like Clicking (Anti-Ban)**:
  - สุ่มพิกัดเบี่ยงเบน (±1% - 3%)
  - สุ่มระยะเวลาหน่วงก่อนกด (Variable Delay 0.05-0.15 วิ)
  - จำลองระยะเวลาการกดนิ้วค้าง (Touch Hold 0.05 วิ) ก่อนยกนิ้ว
- **4-Step Auto Flow**:
  1. **Lobby**: สแกนหาความปลอดภัย, เคลมโบราณวัตถุ
  2. **Prep**: สุ่ม Boosters อัตโนมัติจนกว่าจะได้ "Double Coins"
  3. **Gameplay**: พุ่งตัวออก, ชนไม้ 1, ใช้ไม้ 2 นินจา, กระโดดหลบเหวและเก็บเหรียญบนฟ้า
  4. **Result**: บล็อกการกดพลาดเสียเพชรฟ้าเพื่อชุบชีวิต, เปิดของขวัญ และวนลูป

## ⚙️ ความต้องการของระบบ (Requirements)
1. **Python 3.8+**
2. **Tesseract OCR**: 
   - ดาวน์โหลดได้จาก: [UB-Mannheim Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - ติดตั้งเสร็จแล้ว ให้ระบุ Path ลงใน `config.py` (ปกติจะอยู่ที่ `C:\Program Files\Tesseract-OCR\tesseract.exe`)
3. **Emulator**: แนะนำ LDPlayer 9 หรือ MuMu Player X (ค่าเริ่มต้นตั้งไว้ที่ LDPlayer 9)

## 🛠️ วิธีการติดตั้ง (Installation)
1. ติดตั้งไลบรารีที่จำเป็นผ่าน pip:
   ```bash
   pip install -r requirements.txt
   ```
2. แก้ไขไฟล์ `config.py` เพื่อตั้งค่า Tesseract Path, Window Name และขนาดจอเริ่มต้นของคุณ
3. รันโปรแกรมหลัก:
   ```bash
   python main.py
   ```

## 📂 โครงสร้างโฟลเดอร์
- `main.py`: ลูปการทำงานหลัก (State Machine) ของบอท
- `config.py`: ตั้งค่าคงที่ (Constants) และพิกัด 
- `core/emulator.py`: ควบคุมและค้นหา Window Handle ของโปรแกรมจำลอง
- `core/controller.py`: ระบบกดคลิกแบบสุ่ม (Human-Like Clicking)
- `core/vision.py`: ระบบจับภาพหน้าจอ, สแกนสีพิกเซล, ขยายสเกล และ OCR
