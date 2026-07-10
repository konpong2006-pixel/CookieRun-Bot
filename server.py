import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from bot_engine import bot_instance
import webbrowser
import threading
import time
import sys
import os

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)
    
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ai')
def ai_dashboard():
    return render_template('ai_dashboard.html')

@app.route('/api/stream')
def stream_video():
    def generate():
        while True:
            if hasattr(bot_instance, 'latest_frame_bytes') and bot_instance.latest_frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + bot_instance.latest_frame_bytes + b'\r\n')
            time.sleep(0.1)
    from flask import Response
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/start', methods=['POST'])
def start_bot():
    data = request.json
    mode = data.get('mode', 'COIN')
    use_relay = data.get('use_relay', False)
    use_fast_start = data.get('use_fast_start', False)
    episode = data.get('episode', 'ep1')
    if bot_instance.running:
        return jsonify({"status": "error", "message": "Bot is already running!"}), 400
    
    bot_instance.start(mode=mode, use_relay=use_relay, use_fast_start=use_fast_start, episode=episode)
    return jsonify({"status": "success", "message": f"Started {mode} farm"})

@app.route('/api/reset_ai', methods=['POST'])
def reset_ai():
    data = request.json
    episode = data.get('episode', 'ep1')
    if hasattr(bot_instance, 'ai'):
        bot_instance.ai.reset_memory(episode)
        return jsonify({"status": "success", "message": f"AI memory for {episode} has been reset."})
    return jsonify({"status": "error", "message": "AI module not found."}), 400

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    if not bot_instance.running:
        return jsonify({"status": "error", "message": "Bot is not running!"}), 400
    
    bot_instance.stop()
    return jsonify({"status": "success", "message": "Bot stopped"})

@app.route('/api/shutdown', methods=['POST'])
def shutdown_server():
    if bot_instance.running:
        bot_instance.stop()
    
    def kill_server():
        time.sleep(1.0)
        os._exit(0)
        
    threading.Thread(target=kill_server).start()
    return jsonify({"status": "success", "message": "Server shutting down..."})

@app.route('/api/status', methods=['GET'])
def get_status():
    status = bot_instance.get_status()
    status["use_relay"] = getattr(bot_instance, "use_relay", False)
    return jsonify(status)

@app.route('/api/ai_stats', methods=['GET'])
def get_ai_stats():
    if hasattr(bot_instance, 'ai'):
        return jsonify(bot_instance.ai.get_stats())
    return jsonify({"runs": [], "total_learned": 0, "best_duration": 0})

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.json
    coin_timeout = data.get('coin_timeout')
    box_timeout = data.get('box_timeout')
    use_timeout = data.get('use_timeout')
    use_relay = data.get('use_relay')
    emulator_title = data.get('emulator_title')
    
    try:
        if coin_timeout:
            bot_instance.coin_timeout = int(coin_timeout)
        if box_timeout:
            bot_instance.box_timeout = int(box_timeout)
        if use_timeout is not None:
            bot_instance.use_timeout = bool(use_timeout)
        if use_relay is not None:
            bot_instance.use_relay = bool(use_relay)
        if emulator_title:
            bot_instance.emulator_title = emulator_title
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid timeout value"}), 400
        
    return jsonify({"status": "success", "message": "Settings updated"})

@app.route('/api/reset_stats', methods=['POST'])
def reset_stats():
    bot_instance.reset_stats()
    return jsonify({"status": "success", "message": "Stats reset"})

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == '__main__':
    print("🚀 Starting Web Dashboard on http://127.0.0.1:5000")
    # เปิดเบราว์เซอร์อัตโนมัติ
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
