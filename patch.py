import codecs

with codecs.open('bot_engine.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('\r\n', '\n')

old_lobby = """                    if self.current_state == "LOBBY":
                        self.status_msg = "Checking Lobby status..."
                        
                        # กดกึ่งกลางหน้าจอ 1 ครั้งเสมอเมื่อเข้า Lobby เพื่อปิด Level Up Popup หรือ Daily Login
                        controller.click_percent(50.0, 85.0)
                        time.sleep(1.0)
                        
                        if self.farm_mode == "BOX_RELIC" and vision.has_get_sign(img, LOBBY_RELIC_GET_AREA):"""

new_lobby = """                    if self.current_state == "LOBBY":
                        self.status_msg = "Checking Lobby status..."
                        
                        if self.farm_mode == "BOX_RELIC" and vision.has_get_sign(img, LOBBY_RELIC_GET_AREA):"""

content = content.replace(old_lobby, new_lobby)

content = content.replace('\n', '\r\n')

with codecs.open('bot_engine.py', 'w', 'utf-8') as f:
    f.write(content)

print("Patch successful!")
