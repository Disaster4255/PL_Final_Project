# FRC Scouting App

A Django web application for FRC (FIRST Robotics Competition) scouting and team analysis.
Please scroll down for the Mandarin version.

## Features

- Event and match management via The Blue Alliance API
- Real-time team statistics from Statbotics
- Match scouting with detailed reports (auto, teleop, endgame)
- Match predictions with XP rewards
- Offline QR code submission support
- Pick list generation with combined analytics
- User roles: Admin, Strategist, Scouter
- Gamified XP and leveling system

## Quick Setup

### 1. Install Dependencies
Open the terminal and install the dependencies.
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in project root:
```
TBA_API_KEY=your_tba_api_key_here
```

Get your TBA API key: https://www.thebluealliance.com/account

### 3. Initialize Database

```bash
python manage.py migrate
python manage.py createsuperuser
python setup_admin.py  # Optional: Create test users
```

### 4. Run Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

## Usage

1. **Import Event**: Create event with TBA event key (e.g., "2024mrcmp")
2. **Assign Scouters**: Auto-assign or manually assign to matches
3. **Submit Reports**: Scouters fill out match observations
4. **Predict Matches**: Make predictions before matches start
5. **Generate QR Codes**: For offline submissions
6. **Complete Matches**: Mark matches complete and verify predictions
7. **View Analytics**: Team stats, EPA data, and pick lists

## Project Structure

```
frc_scouting/     # Django settings
accounts/         # User authentication and profiles
analytics/        # Statbotics integration and analytics
events/           # Event and match management
scouting/         # Scouting reports and predictions
templates/        # HTML templates
```

## Tech Stack

- Django 6.0
- SQLite database
- The Blue Alliance API (tbapy 1.3.2)
- Statbotics API (statbotics 3.0.0)
- Python standard library (no external dependencies for QR codes)

## Production Deployment

For production deployment:
1. Set `DEBUG=False` in settings
2. Configure proper `SECRET_KEY`
3. Use PostgreSQL instead of SQLite
4. Set up proper static file serving
5. Configure ALLOWED_HOSTS
6. Use environment variables for sensitive data

## License

MIT License





# FRC 偵查分析應用程式 (FRC Scouting App)

A Django web application for FRC (FIRST Robotics Competition) scouting and team analysis. (一個用於 FRC (FIRST 機器人競賽) 偵查與隊伍分析的 Django 網頁應用程式。)

## 功能 (Features)

- Event and match management via The Blue Alliance API (透過 The Blue Alliance API 進行賽事與比賽管理)
- Real-time team statistics from Statbotics (來自 Statbotics 的即時隊伍統計數據)
- Match scouting with detailed reports (auto, teleop, endgame) (附帶詳細報告的比賽偵查 (自動階段、遙控階段、終局))
- Match predictions with XP rewards (提供經驗值 (XP) 獎勵的比賽預測)
- Offline QR code submission support (支援離線 QR Code 提交資料)
- Pick list generation with combined analytics (結合分析數據的選秀名單 (Pick list) 生成)
- User roles: Admin, Strategist, Scouter (使用者角色：管理員 (Admin)、策略師 (Strategist)、偵查員 (Scouter))
- Gamified XP and leveling system (遊戲化經驗值 (XP) 與等級系統)

## 快速設定 (Quick Setup)

### 1. 安裝依賴項 (Install Dependencies)
打開終端機並安裝依賴項目
```bash
python -m venv venv
venv\Scripts\activate  # Windows (Windows)
# source venv/bin/activate  # Linux/Mac (Linux/Mac)

pip install -r requirements.txt
```

### 2. 配置環境 (Configure Environment)
Create .env file in project root: (在專案根目錄中創建 .env 檔案：)

TBA_API_KEY=your_tba_api_key_here
Get your TBA API key: (請至此處獲取您的 TBA API 金鑰：) https://www.thebluealliance.com/account

### 3. 初始化資料庫 (Initialize Database)
Bash
```
python manage.py migrate
python manage.py createsuperuser
python setup_admin.py  # Optional: Create test users (選項：創建測試使用者)
```

### 4. 運行伺服器 (Run Server)
Bash
```
python manage.py runserver
Visit: http://localhost:8000 (訪問：http://localhost:8000)
```

## 使用方法 (Usage)
Import Event (匯入賽事): Create event with TBA event key (e.g., "2024mrcmp") (使用 TBA 賽事代碼創建賽事 (例如："2024mrcmp"))

Assign Scouters (分配偵查員): Auto-assign or manually assign to matches (自動或手動分配偵查員到各個比賽)

Submit Reports (提交報告): Scouters fill out match observations (偵查員填寫比賽觀察報告)

Predict Matches (預測比賽): Make predictions before matches start (在比賽開始前進行預測)

Generate QR Codes (生成 QR Code): For offline submissions (用於離線提交資料)

Complete Matches (完成比賽): Mark matches complete and verify predictions (標記比賽完成並驗證預測結果)

View Analytics (查看分析): Team stats, EPA data, and pick lists (查看隊伍統計數據、EPA 資料和選秀名單)

## 專案結構 (Project Structure)
frc_scouting/     # Django settings (Django 設定)
accounts/         # User authentication and profiles (使用者驗證和個人資料)
analytics/        # Statbotics integration and analytics (Statbotics 整合與分析)
events/           # Event and match management (賽事與比賽管理)
scouting/         # Scouting reports and predictions (偵查報告與預測)
templates/        # HTML templates (HTML 模板)

## 技術堆疊 (Tech Stack)
Django 6.0

SQLite database (SQLite 資料庫)

The Blue Alliance API (tbapy 1.3.2)

Statbotics API (statbotics 3.0.0)

Python standard library (no external dependencies for QR codes) (Python 標準函式庫 (QR Code 無外部依賴項))

## 生產環境部署 (Production Deployment)
For production deployment: (對於生產環境部署：)

Set DEBUG=False in settings (在設定中將 DEBUG 設置為 False)

Configure proper SECRET_KEY (配置正確的 SECRET_KEY)

Use PostgreSQL instead of SQLite (使用 PostgreSQL 而非 SQLite)

Set up proper static file serving (設定正確的靜態檔案服務)

Configure ALLOWED_HOSTS (配置 ALLOWED_HOSTS)

Use environment variables for sensitive data (對敏感資料使用環境變數)

## 授權 (License)
MIT License (MIT 授權)