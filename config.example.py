"""Copy this file to config.py and fill in your real values."""

TESLA_CLIENT_ID = ""
TESLA_CLIENT_SECRET = ""

TESLA_REGION = "cn"
TESLA_REDIRECT_URI = "https://your-domain.com/tesla/callback"
TESLA_PARTNER_DOMAIN = "your-domain.com"

TESLA_AUTHORIZE_URL = "https://auth.tesla.cn/oauth2/v3/authorize"
TESLA_TOKEN_URL = "https://auth.tesla.cn/oauth2/v3/token"
TESLA_FLEET_API_BASE = "https://fleet-api.prd.cn.vn.cloud.tesla.cn"
TESLA_AUDIENCE = TESLA_FLEET_API_BASE

DEFAULT_SCOPES = [
    "openid",
    "offline_access",
    "user_data",
    "vehicle_device_data",
    "vehicle_location",
    "vehicle_cmds",
    "vehicle_charging_cmds",
]

MYSQL_CONFIG = {
    "host": "",
    "port": 3306,
    "user": "",
    "password": "",
    "database": "",
    "charset": "utf8mb4",
    "autocommit": True,
}

# OAuth/Token refresh guard window.
TOKEN_REFRESH_BEFORE_MINUTES = 10

# FastAPI
APP_HOST = "0.0.0.0"
APP_PORT = 8000
DEBUG = True
CORS_ALLOW_ORIGINS = [
    "http://localhost:5173",
]

# Amap (高德地图)
AMAP_KEY = ""

# LLM (OpenAI compatible)
LLM_API_KEY = ""
LLM_BASE_URL = ""
LLM_MODEL = ""

# TTS (Xiaomi Mimo)
TTS_API_KEY = LLM_API_KEY
TTS_BASE_URL = LLM_BASE_URL

TTS_MODEL = "mimo-v2-tts"
TTS_VOICE = "default_en"
TTS_RESPONSE_FORMAT = "pcm16"

# Auth (single user)
AUTH_USERNAME = "admin"
# Run: python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
AUTH_PASSWORD_HASH = "<bcrypt hash of your password>"
JWT_SECRET = "<your JWT secret key>"
JWT_EXPIRE_HOURS = 72

# Fleet Telemetry (official flow via vehicle-command proxy)
FLEET_TELEMETRY_PROXY_BASE = "https://127.0.0.1:4443"
FLEET_TELEMETRY_PROXY_TIMEOUT = 20
FLEET_TELEMETRY_PROXY_VERIFY_SSL = False
FLEET_TELEMETRY_INGEST_SECRET = ""
