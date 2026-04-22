# Tesla CN App

基于 FastAPI 的 Tesla 中国 Fleet API 集成服务，提供 OAuth 认证、车辆控制、行程分析及 AI 智能对话功能。

## 功能特性

- **OAuth 认证** — 适配中国区 `auth.tesla.cn`，支持授权码交换与 Token 自动刷新
- **Partner 账号管理** — 合作伙伴注册、公钥同步
- **车辆管理** — 同步车辆数据、查询车辆状态（电量、位置、空调等）
- **车辆控制** — 锁车、解锁、开启前后备箱（签名指令）
- **AI 助手** — 基于 Xiaomi Mimo 大模型的 SSE 流式对话，支持 18 种工具调用（车辆控制、地图搜索、导航等）
- **行程分析** — 基于遥测数据的行程统计，含 Haversine 距离计算与驻停检测
- **TTS 语音合成** — 将文本转为 PCM16/WAV 语音输出
- **Fleet Telemetry** — 支持 Tesla 官方遥测数据配置与接入
- **前端 SPA** — Vue 3 + Vite 单页应用

## 技术栈

| 组件 | 技术 |
|---|---|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | MySQL (PyMySQL) |
| AI 模型 | Xiaomi Mimo LLM (OpenAI 兼容接口) |
| 地图服务 | 高德地图 API (POI 搜索、逆地理编码) |
| Tesla API | tesla-fleet-api v1.4.5 + 自研 CN OAuth |
| 前端 | Vue 3 + Vite |
| 认证 | JWT (python-jose + bcrypt) |

## 项目结构

```
├── main.py                 # FastAPI 入口，路由注册 + SPA 静态托管
├── config.example.py       # 配置模板（复制为 config.py 后填写）
├── ddl.sql                 # MySQL 建表脚本（8 张表）
├── requirements.txt        # Python 依赖
├── app/
│   ├── routers/            # API 路由（auth、agent、telemetry、fleet_telemetry）
│   ├── services/           # 业务逻辑层
│   ├── repositories/       # 数据持久化层（原生 SQL）
│   ├── tesla/              # Tesla API 客户端（认证、合作伙伴、Fleet）
│   ├── utils/              # 工具类（JWT 签发等）
│   └── exceptions.py       # 自定义异常层级
├── frontend/
│   ├── src/                # Vue 3 前端源码
│   └── dist/               # 构建产物
└── docs/                   # 使用文档与示例
```

## 快速开始

### 1. 环境准备

- Python 3.10+
- MySQL 8.0+
- Node.js 18+（如需构建前端）
- EC SECP256R1 密钥对（`private-key.pem`），将私钥文件放在项目根目录。公钥需通过 `https://你的域名/.well-known/appspecific/com.tesla.3p.public-key.pem` 可访问。生成方式参考 [Tesla Fleet API 接入指南](docs/tesla-fleet-api-setup.md)。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 创建数据库并执行 DDL

```bash
mysql -u root -p your_database < ddl.sql
```

### 4. 配置

复制配置模板并填写你的实际配置：

```bash
cp config.example.py config.py
```

编辑 `config.py`，替换以下配置项：

- `TESLA_CLIENT_ID` / `TESLA_CLIENT_SECRET` — 你的 Tesla 开发者应用凭据
- `TESLA_REDIRECT_URI` / `TESLA_PARTNER_DOMAIN` — 对应你的域名
- `MYSQL_CONFIG` — 数据库连接信息
- `JWT_SECRET` — JWT 签名密钥（随机字符串即可）
- `AUTH_PASSWORD_HASH` — 管理员密码的 bcrypt 哈希，可执行以下命令生成：
  ```bash
  python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
  ```

> `config.py` 已加入 `.gitignore`，不会被版本控制。

### 5. 构建前端

```bash
cd frontend
npm install
npm run build
```

开发模式使用 `npm run dev` 启动 Vite 开发服务器。

### 6. 启动服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后默认自动创建管理员账户 `admin`（密码在 `config.py` 中配置）。

## API 接口

| 接口 | 说明 |
|---|---|
| `POST /api/auth/login` | JWT 登录 |
| `POST /api/auth/register` | 用户注册 |
| `GET /tesla/partner/setup` | 注册 Tesla 合作伙伴账号 |
| `GET /tesla/partner/public-key` | 同步合作伙伴公钥 |
| `GET /tesla/login` | 获取授权 URL |
| `GET /tesla/login-redirect` | 跳转至 Tesla 登录页 |
| `GET /tesla/callback` | OAuth 回调（授权码交换） |
| `GET /tesla/token/latest` | 获取最新用户 Token |
| `GET /tesla/vehicles` | 获取车辆列表 |
| `GET /tesla/vehicles/{vin}/status` | 查询车辆状态 |
| `POST /tesla/vehicles/{vin}/lock` | 锁车 |
| `POST /tesla/vehicles/{vin}/unlock` | 解锁 |
| `POST /tesla/vehicles/{vin}/trunk/{rear\|front}` | 开/关后备箱 |
| `POST /api/agent/chat` | SSE 流式 AI 对话 |
| `GET /api/agent/greeting` | 获取车辆状态用于问候语 |
| `POST /api/agent/tts` | 文本转语音 |
| `POST /api/telemetry/ingest` | 遥测数据写入 |
| `GET /api/telemetry/trips/summary` | 行程分析汇总 |
| `POST /api/fleet-telemetry/configure` | 配置 Tesla 官方遥测 |
| `POST /api/fleet-telemetry/ingest` | 接收官方遥测数据 |

以 `/tesla/vehicles` 开头的接口需要 JWT 认证。

## 架构说明

Tesla 中国区 API 的端点与国际区不同（`auth.tesla.cn` / `fleet-api.prd.cn.vn.cloud.tesla.cn`），而第三方库 `tesla-fleet-api` 的 Token 端点硬编码为 `.com` 域名。因此本项目采用混合架构：

- **OAuth / Token 交换与刷新** — 自定义代码调用 `auth.tesla.cn`
- **车辆 API 调用** — 通过 `tesla-fleet-api` 库使用 `api.products()`（注意 `api.vehicles.list()` 在 v1.4.5 对中国区不可用）
- **合作伙伴管理** — 自定义代码调用 CN Fleet API 基础 URL

## 文档

- [Tesla Fleet API 接入指南](docs/tesla-fleet-api-setup.md)
- [AI 助手工具调用示例](docs/agent-commands-example.md)
- [遥测与行程分析示例](docs/telemetry-trip-example.md)
- [初始化流程](docs/init-example.md)

## License

MIT
