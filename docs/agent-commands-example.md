# Agent Vehicle Commands Example

## Start charging

```bash
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"start charging\"}]}"
```

## Stop charging

```bash
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"stop charging\"}]}"
```

## Window control

```bash
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"close all windows\"}]}"
```

Notes:
- Current Tesla Fleet API only supports `vent`/`close` at all-window scope.
- If user asks for one specific window (for example `front_left`), the agent returns an explicit unsupported message.

## More control examples

```bash
# wake vehicle
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"wake up the car\"}]}"

# flash lights
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"flash the lights\"}]}"

# honk horn
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"honk the horn\"}]}"

# turn climate on / off
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"turn climate on\"}]}"
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"turn climate off\"}]}"

# charge port open / close
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"open charge port\"}]}"
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"close charge port\"}]}"

# set charge limit
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"set charge limit to 80%\"}]}"

# sentry mode on / off
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"turn sentry mode on\"}]}"
curl -N -X POST "http://127.0.0.1:8000/api/agent/chat" -H "Authorization: Bearer <your_jwt_token>" -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"turn sentry mode off\"}]}"
```
