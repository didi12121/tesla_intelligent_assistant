const API_BASE = ''

export function getToken() {
  return localStorage.getItem('token')
}

export function setToken(token) {
  localStorage.setItem('token', token)
}

export function clearToken() {
  localStorage.removeItem('token')
}

function headers() {
  const token = getToken()
  const h = { 'Content-Type': 'application/json' }
  if (token) h['Authorization'] = `Bearer ${token}`
  return h
}

export async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, { headers: headers() })
  if (res.status === 401) {
    clearToken()
    throw new Error('未授权，请重新登录')
  }
  return res.json()
}

export async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  })
  if (res.status === 401) {
    clearToken()
    throw new Error('未授权，请重新登录')
  }
  return res
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '登录失败')
  setToken(data.token)
  return data
}

export async function register(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '注册失败')
  return data
}

export async function fetchEventSource(path, body, onMessage) {
  const res = await apiPost(path, body)
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      onMessage(JSON.parse(line.slice(6)))
    }
  }
}

export async function apiPostBlob(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  })
  if (res.status === 401) {
    clearToken()
    throw new Error('未授权，请重新登录')
  }
  if (!res.ok) {
    let msg = '请求失败'
    try {
      const data = await res.json()
      msg = data.detail || msg
    } catch (_) {
      // ignore
    }
    throw new Error(msg)
  }
  return await res.blob()
}
