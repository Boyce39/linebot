from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# ✅ 設定 LINE API 金鑰
LINE_CHANNEL_ACCESS_TOKEN = "iRWhDYwXRiD/RptDDDuyDf9HWlMYradW0fh3FsJ3SjaxQxe/+85g/0EPc4oILjfaDEp0+XRvtfamx+McJq+wIwXRxU9W87/hUiVZ/3dKpUH+qaCiivlGaDEytfNG9becHeP7ohmeg7iWN40uyasvDwdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "8c6c282a4eb5b8f4522dbef0b16d5c38"

# 初始化 LINE SDK
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ 設定 Flask 伺服器
app = Flask(__name__)

# ✅ 設定 Google Drive API
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SERVICE_ACCOUNT_FILE = r"C:\Users\Cyborg 15\Desktop\毅存放專案\程式撰寫\Line Bot\client_secrets.json"

# 確保 JSON 憑證存在
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise FileNotFoundError(f"找不到 Google API 憑證檔案: {SERVICE_ACCOUNT_FILE}")

# 建立 Google Drive 服務
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

# ✅ 設定 Google Drive 主資料夾
GOOGLE_DRIVE_PARENT_FOLDER_ID = "1TQV9-jTb12kR5MaT4k62JVzfAYGA4sg3"

import re

# ✅ 檢查並建立 Google Drive 資料夾
def create_drive_folder(folder_name, parent_folder_id):
    if not parent_folder_id:
        print(f"❌ 錯誤：parent_folder_id 未提供，無法建立資料夾 {folder_name}")
        return None

    # ✅ 確保 folder_name 不含特殊字符，避免 Google Drive API 查詢失敗
    folder_name = re.sub(r'[\/:*?"<>|]', '', folder_name)

    print(f"🔍 嘗試建立或取得資料夾：{folder_name} (父資料夾 ID: {parent_folder_id})")

    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_folder_id}' in parents"

    try:
        response = drive_service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
        files = response.get("files", [])

        if files:
            print(f"📂 資料夾已存在：{folder_name}, ID: {files[0]['id']}")
            return files[0]["id"]  # 如果資料夾已存在，回傳資料夾 ID
        
        # ✅ 建立新資料夾
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields="id").execute()
        print(f"✅ 成功建立資料夾：{folder_name}, ID: {folder['id']}")
        return folder["id"]
    
    except Exception as e:
        print(f"❌ 無法建立資料夾：{folder_name}，錯誤訊息：{e}")
        return None


# ✅ Webhook 路由
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    
    print("✅ 收到 LINE Webhook 訊息：", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ LINE Webhook 簽名驗證失敗！")
        return "Invalid signature", 400

    return "OK", 200

# ✅ 圖片訊息處理器
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        user_id = event.source.user_id
        message_id = event.message.id

        # ✅ 查詢用戶名稱
        try:
            profile = line_bot_api.get_profile(user_id)
            user_name = profile.display_name.strip()
            print(f"🔍 用戶名稱：{user_name}")
        except Exception as e:
            print(f"❌ 無法獲取用戶名稱，錯誤：{e}")
            user_name = user_id  

        # ✅ 下載圖片
        image_path = f"temp/{message_id}.jpg"
        os.makedirs("temp", exist_ok=True)

        try:
            message_content = line_bot_api.get_message_content(message_id)
            with open(image_path, "wb") as f:
                for chunk in message_content.iter_content():
                    f.write(chunk)
            print(f"✅ 圖片已下載：{image_path}")
        except Exception as e:
            print(f"❌ 無法下載圖片，錯誤：{e}")
            return

        # ✅ 檢查或建立當天的資料夾
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        today_folder_id = create_drive_folder(today_str, GOOGLE_DRIVE_PARENT_FOLDER_ID)

        if not today_folder_id:
            print(f"❌ 無法建立當日資料夾 {today_str}")
            return

        # ✅ 檢查或建立用戶的資料夾
        user_folder_id = create_drive_folder(user_name, today_folder_id)

        if not user_folder_id:
            print(f"❌ 無法建立使用者 {user_name} 的資料夾")
            return

        # ✅ 上傳圖片到 Google Drive
        try:
            file_metadata = {
                "name": f"{message_id}.jpg",
                "parents": [user_folder_id]
            }
            media = MediaFileUpload(image_path, mimetype="image/jpeg")
            file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            print(f"📸 圖片已上傳到 Google Drive, ID: {file['id']}")

            # ✅ 回覆使用者
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=f"你的照片已成功上傳！\n已存入資料夾：{today_str} / {user_name}")
            )

        except Exception as e:
            print(f"❌ 圖片上傳失敗，錯誤：{e}")

    except Exception as e:
        print(f"🔥 發生未預期的錯誤，錯誤訊息：{e}")


# ✅ 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=True)  # ✅ 啟用多線程
