from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, FileMessage
import os
import datetime
import subprocess
import time
import threading
import requests

#  LINE API 金鑰
LINE_CHANNEL_ACCESS_TOKEN = ""
LINE_CHANNEL_SECRET = ""

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# 預設檔案儲存路徑
DEFAULT_SAVE_PATH = r"N:\\Line檔案"

if os.path.exists(DEFAULT_SAVE_PATH):
    SAVE_PATH = DEFAULT_SAVE_PATH
else:
    SAVE_PATH = input("未找到預設路徑，請輸入新的存放路徑: ").strip()
    os.makedirs(SAVE_PATH, exist_ok=True)
print(f"使用的存放路徑: {SAVE_PATH}")

# Webhook 路由
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    print("收到 LINE Webhook 訊息：", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("LINE Webhook 驗證失敗！")
        return "Invalid signature", 400

    return "OK", 200

# 處理圖片與檔案
@handler.add(MessageEvent, message=(ImageMessage, FileMessage))
def handle_file_message(event):
    try:
        user_id = event.source.user_id
        message_id = event.message.id
        file_name = "未知檔案"

        try:
            profile = line_bot_api.get_profile(user_id)
            user_name = profile.display_name.strip()
            print(f"用戶名稱：{user_name}")
        except Exception as e:
            print(f"無法獲取用戶名稱，錯誤：{e}")
            user_name = user_id

        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        save_directory = os.path.join(SAVE_PATH, today_str, user_name)
        os.makedirs(save_directory, exist_ok=True)

        if isinstance(event.message, ImageMessage):
            file_name = f"{message_id}.jpg"
        elif isinstance(event.message, FileMessage):
            file_name = event.message.file_name

        file_path = os.path.join(save_directory, file_name)
        try:
            message_content = line_bot_api.get_message_content(message_id)
            with open(file_path, "wb") as f:
                for chunk in message_content.iter_content():
                    f.write(chunk)
            print(f"檔案已下載：{file_path}")
        except Exception as e:
            print(f"無法下載檔案，錯誤：{e}")
    except Exception as e:
        print(f"發生未預期的錯誤，錯誤訊息：{e}")

@app.route("/")
def home():
    return "Flask 伺服器正在運行"

# 啟動 ngrok 並自動更新 webhook

def start_ngrok():
    print("正在啟動 ngrok...")
    ngrok_process = subprocess.Popen(["ngrok", "http", "5000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # time.sleep(5)
    try:
        res = requests.get("http://localhost:4040/api/tunnels").json()
        public_url = res['tunnels'][0]['public_url']
        print(f"API公開網址：{public_url}/callback")
        # 自動更新 LINE webhook URL
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "endpoint": f"{public_url}/callback"
        }
        response = requests.put("https://api.line.me/v2/bot/channel/webhook/endpoint", json=data, headers=headers)
        print(f"更新 LINE Webhook URL 結果: {response.status_code} {response.text}")

    return ngrok_process

if __name__ == "__main__":
    ngrok_thread = threading.Thread(target=start_ngrok)
    ngrok_thread.start()
    app.run(port=5000, debug=True)


#pyinstaller --onefile --name=linebot_app --hidden-import=requests --hidden-import=linebot testin.py
