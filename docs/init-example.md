# Tesla CN Initialization Example

## 1. Start API server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 2. Run one-shot partner initialization

```bash
curl -X GET "http://127.0.0.1:8000/tesla/init"
```

This call does both:
- Register partner account
- Sync partner public key to local MySQL

## 3. Continue OAuth flow

```bash
curl -X GET "http://127.0.0.1:8000/tesla/login-redirect?token=<your_jwt_token>"
```
