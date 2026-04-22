# Tesla Fleet API 服务注册与使用流程

## 前置条件

1. 拥有 Tesla 开发者账号，在 [developer.tesla.cn](https://developer.tesla.cn) 创建应用
2. 拥有一个可公网访问的域名（用于 OAuth 回调和公钥托管）
3. 生成 EC SECP256R1 密钥对，将 `private-key.pem` 放在项目根目录，公钥需通过 `https://你的域名/.well-known/appspecific/com.tesla.3p.public-key.pem` 可访问
4. MySQL 数据库已初始化（执行 `ddl.sql`）

## 注册流程（首次部署时执行）

按顺序调用以下接口，**每个接口只需调用一次**：

### 1. 注册 Partner 账号

```
GET /tesla/partner/setup
```

将你的域名注册到 Tesla 的 partner account 系统。内部调用 `POST /api/1/partner_accounts`，使用 `client_credentials` 授权获取 partner token，并将结果保存到 `tesla_partner_account` 表。

### 2. 同步公钥

```
GET /tesla/partner/public-key
```

从 Tesla 拉取已注册的公钥信息并保存到本地。这一步确认公钥已被 Tesla 正确识别。

> 如果更换了密钥对，需要重新执行步骤 1 和 2。

### 3. 用户 OAuth 授权

```
GET /tesla/login-redirect
```

跳转到 Tesla 授权页面，用户登录并授权后，Tesla 会回调：

```
GET /tesla/callback?code=xxx&state=yyy
```

回调接口自动用 `code` 换取 access_token 和 refresh_token，保存到 `tesla_third_party_token` 表。

## 日常使用

用户授权完成后，以下车辆操作接口可直接使用，**无需额外维护**：

| 接口 | 功能 |
|------|------|
| `GET /tesla/vehicles` | 列出车辆 |
| `GET /tesla/vehicles/{vin}/status` | 查询车辆状态（电量、温度、车门、哨兵模式等） |
| `GET /tesla/vehicles/{vin}/lock` | 锁车 |
| `GET /tesla/vehicles/{vin}/unlock` | 解锁 |
| `GET /tesla/vehicles/{vin}/trunk/rear` | 操作后尾箱 |
| `GET /tesla/vehicles/{vin}/trunk/front` | 操作前备箱 |

## Token 自动刷新机制

### User Token（用户级）

每次车辆操作都会调用 `ensure_third_party_token()`：
- 检查 `access_token` 是否在过期窗口内（默认过期前 10 分钟）
- 未过期 → 直接使用
- 已过期 → 用 `refresh_token` 自动换取新 token，写入数据库

**无需手动干预，全自动。**

### Partner Token（应用级）

partner token 仅在 `/tesla/partner/setup` 和 `/tesla/partner/public-key` 接口内部使用：
- 调用时会通过 `ensure_partner_token()` 检查并自动刷新
- 日常车辆操作不依赖 partner token

**日常使用无需关注，只有重新注册/同步公钥时才会用到。**

## 聊天 Agent

应用集成了 LLM Agent，支持自然语言控制车辆：

```
POST /api/agent/chat    — 流式聊天（SSE），支持 tool calling
GET  /api/agent/greeting — 获取车辆状态用于打招呼
```

支持的操作：查询状态、锁车、解锁、开关后备箱。

前端通过 Vue SPA 提供聊天界面，登录后使用（用户名密码见 `config.py`）。

## 关键配置（config.py）

| 配置项 | 说明 |
|--------|------|
| `TESLA_CLIENT_ID` / `TESLA_CLIENT_SECRET` | Tesla 应用凭证 |
| `TESLA_REDIRECT_URI` | OAuth 回调地址 |
| `TESLA_PARTNER_DOMAIN` | 注册的域名 |
| `DEFAULT_SCOPES` | OAuth 授权范围 |
| `LLM_*` | LLM 接口配置 |
| `AUTH_USERNAME` / `AUTH_PASSWORD_HASH` | 前端登录账号 |
| `MYSQL_CONFIG` | 数据库连接 |

## 已知限制

- `tesla-fleet-api` v1.4.5：`api.vehicles.list()` 在中国区不可用，需用 `api.products()` 代替
- 车辆命令（锁车、解锁、后备箱）需要 signed 命令（`createSigned`），车辆需开启 `command_signing: "required"`
- 车辆位置数据需要 `vehicle_location` scope，授权时需包含
