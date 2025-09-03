# LINE Bot - 檔案自動備份機器人

## 專案介紹

這是一個使用 Python 和 Flask 框架開發的 LINE Bot，其主要功能是自動接收並歸檔使用者傳送的圖片與檔案。

當使用者傳送任何圖片或檔案給這個 Bot 時，它會自動在指定的路徑下，以「日期」和「使用者名稱」建立資料夾，並將檔案儲存其中，方便日後查找與管理。

此專案還整合了 `ngrok`，能夠在啟動時自動建立一個公開的網址，並設定為 LINE Bot 的 Webhook，大幅簡化了在本機開發與測試的流程。

## 主要功能

- **自動歸檔**：自動下載並儲存使用者傳送的圖片與檔案。
- **智慧資料夾結構**：以 `年-月-日/使用者名稱/` 的結構組織檔案，一目了然。
- **Flask 網頁伺服器**：使用輕量級的 Flask 框架接收 LINE Webhook 事件。
- **整合 Ngrok**：啟動時自動建立 `ngrok` 通道，並將公開網址更新到 LINE Developer 後台，無需手動設定。
- **可打包為執行檔**：專案中包含 `.spec` 檔案，可使用 PyInstaller 打包成單一執行檔，方便部署。

---

## ⚠️ 可存在的資安風險

目前的程式碼 (`LINEbotv1.py`) 將 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` **直接寫在程式碼中**。這是一種不安全的做法，可能會導致您的金鑰外洩。

**強烈建議**修改程式碼，改用**環境變數 (Environment Variables)** 或其他安全的金鑰管理方式來讀取您的憑證。

---

## 檔案結構

- `LINEbotv1.py`: 主要的應用程式腳本。
- `ngrok.exe`: 用於建立內網穿透通道的工具，讓 LINE 的伺服器能連線到您的本機電腦。
- `linebot_app.spec`: PyInstaller 的設定檔，用於將專案打包成 `.exe` 執行檔。

## 環境需求

- Python 3
- `ngrok` 執行檔 (需與腳本放在同一目錄，或已設定在系統環境變數中)
- Python 函式庫:
  - `Flask`
  - `line-bot-sdk-python`
  - `requests`

您可以使用 pip 來安裝所有相依套件：
```bash
pip install Flask line-bot-sdk-python requests
```

## 設定與使用步驟

1.  **安裝相依套件**：執行上面的 `pip install` 指令。

2.  **設定 API 金鑰**：
    - 打開 `LINEbotv1.py` 檔案。
    - 將 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 的值換成您自己的 Bot 金鑰。

3.  **設定存檔路徑**：
    - 程式預設的存檔路徑為 `N:\Line檔案`。
    - 如果此路徑不存在，程式會在啟動時要求您手動輸入一個新的有效路徑。

4.  **執行 Bot**：
    - 在終端機中執行 `python LINEbotv1.py`。
    - 程式會啟動 Flask 伺服器，並自動執行 ngrok 取得公開網址。

5.  **測試**：
    - 待程式顯示 `更新 LINE Webhook URL 結果: 200` 後，表示設定成功。
    - 直接在 LINE 中傳送圖片或檔案給您的 Bot，檔案將會被自動下載並儲存。

## (可選) 建立執行檔

如果您想將此專案打包成一個獨立的 `.exe` 執行檔，可以執行：

```bash
# 先安裝 pyinstaller
pip install pyinstaller

# 使用 .spec 檔案進行打包
pyinstaller linebot_app.spec
```
