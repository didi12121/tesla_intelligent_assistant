<template>
  <!-- 登录页面 -->
  <div v-if="!isLoggedIn" class="login-page">
    <div class="login-card">
      <div class="login-logo">T</div>
      <h1>Tesla 智能助手</h1>
      <p class="login-subtitle">{{ showRegister ? '注册新账号' : '登录以管理你的车辆' }}</p>

      <!-- 登录表单 -->
      <form v-if="!showRegister" @submit.prevent="doLogin">
        <input
          v-model="loginForm.username"
          type="text"
          placeholder="用户名"
          autocomplete="username"
        />
        <input
          v-model="loginForm.password"
          type="password"
          placeholder="密码"
          autocomplete="current-password"
        />
        <div v-if="loginError" class="login-error">{{ loginError }}</div>
        <button type="submit" :disabled="loginLoading">
          {{ loginLoading ? '登录中...' : '登录' }}
        </button>
        <div class="login-switch">
          没有账号？<a href="#" @click.prevent="showRegister = true; loginError = ''">注册</a>
        </div>
      </form>

      <!-- 注册表单 -->
      <form v-else @submit.prevent="doRegister">
        <input
          v-model="registerForm.username"
          type="text"
          placeholder="用户名"
          autocomplete="username"
        />
        <input
          v-model="registerForm.password"
          type="password"
          placeholder="密码（至少6位）"
          autocomplete="new-password"
        />
        <input
          v-model="registerForm.confirmPassword"
          type="password"
          placeholder="确认密码"
          autocomplete="new-password"
        />
        <div v-if="loginError" class="login-error">{{ loginError }}</div>
        <button type="submit" :disabled="loginLoading">
          {{ loginLoading ? '注册中...' : '注册' }}
        </button>
        <div class="login-switch">
          已有账号？<a href="#" @click.prevent="showRegister = false; loginError = ''">登录</a>
        </div>
      </form>
    </div>
  </div>

  <!-- 未绑定 Tesla 的引导页 -->
  <template v-else-if="!isBound">
    <div class="login-page">
      <div class="login-card">
        <div class="login-logo">T</div>
        <h1>绑定 Tesla 账号</h1>
        <p class="login-subtitle">请授权你的 Tesla 账号以使用智能助手</p>
        <div v-if="bindError" class="login-error">{{ bindError }}</div>
        <button @click="startBind" :disabled="binding">
          {{ binding ? '跳转中...' : '授权 Tesla 账号' }}
        </button>
        <button class="logout-btn" style="margin-top: 12px; width: 100%;" @click="doLogout">退出登录</button>
      </div>
    </div>
  </template>

  <!-- 聊天页面 -->
  <template v-else>
    <div class="chat-header">
      <div>
        <h1>Tesla 智能助手</h1>
        <div class="subtitle" v-if="vin">{{ vin.slice(0, 3) + '***********' + vin.slice(-4) }}</div>
      </div>
      <div class="header-actions">
        <label class="tts-toggle">
          <input type="checkbox" v-model="voiceMode" />
          语音播报
        </label>
        <a class="key-btn" href="https://www.tesla.com/_ak/v345x21968.zicp.fun" target="_blank" rel="noopener">添加虚拟钥匙</a>
        <button class="logout-btn" @click="doLogout">退出</button>
      </div>
    </div>

    <div class="messages" ref="messagesRef">
      <div v-if="loading" class="loading">正在连接车辆...</div>
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="avatar">{{ msg.role === 'user' ? '你' : 'T' }}</div>
        <div>
          <div class="bubble">{{ msg.content }}</div>
          <div v-if="msg.toolCall" class="tool-indicator">
            <div class="spinner"></div>
            {{ msg.toolCall }}
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <input
        v-model="input"
        @keydown.enter="send"
        placeholder="说点什么... 比如「帮我锁车」「看看续航」"
        :disabled="sending"
      />
      <button @click="send" :disabled="sending || !input.trim()">
        {{ sending ? '发送中' : '发送' }}
      </button>
    </div>
  </template>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { getToken, clearToken, login as apiLogin, register as apiRegister, apiGet, fetchEventSource, apiPostBlob } from './api.js'

const isLoggedIn = ref(false)
const isBound = ref(false)
const showRegister = ref(false)
const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', password: '', confirmPassword: '' })
const loginError = ref('')
const loginLoading = ref(false)
const bindError = ref('')
const binding = ref(false)

const messages = ref([])
const input = ref('')
const sending = ref(false)
const loading = ref(true)
const vin = ref('')
const messagesRef = ref(null)
const voiceMode = ref(localStorage.getItem('voice_mode') === '1')
const currentAudio = ref(null)
const currentAudioUrl = ref('')
const ttsSegmentBuffer = ref('')
const ttsTextQueue = ref([])
const ttsQueueRunning = ref(false)
const ttsPlaybackRate = ref(Number(localStorage.getItem('tts_playback_rate') || '3.0'))

const chatHistory = []
const userLocation = ref(null)

watch(voiceMode, (enabled) => {
  localStorage.setItem('voice_mode', enabled ? '1' : '0')
  if (!enabled) {
    stopAudioPlayback()
    clearTtsQueue()
  }
})

watch(ttsPlaybackRate, (rate) => {
  localStorage.setItem('tts_playback_rate', String(rate))
})

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function formatStatus(status) {
  const d = status.data || status
  const charge = d.charge || {}
  const climate = d.climate || {}
  const vs = d.vehicle_state || {}

  const lines = []
  if (charge.battery_level != null) lines.push(`电量 ${charge.battery_level}%，续航 ${charge.battery_range?.toFixed(1) || '-'} km`)
  if (charge.charging_state) lines.push(`充电状态: ${charge.charging_state}`)
  if (climate.inside_temp != null) lines.push(`车内 ${climate.inside_temp}°C，车外 ${climate.outside_temp ?? '-'}°C`)
  if (vs.sentry_mode != null) lines.push(`哨兵模式: ${vs.sentry_mode ? '已开启' : '已关闭'}`)
  if (vs.locked != null) lines.push(`车门: ${vs.locked ? '已锁' : '未锁'}`)
  if (d.state) lines.push(`车辆状态: ${d.state}`)
  return lines.join('\n')
}

async function doLogin() {
  loginError.value = ''
  loginLoading.value = true
  try {
    await apiLogin(loginForm.value.username, loginForm.value.password)
    isLoggedIn.value = true
    await checkBindStatus()
  } catch (e) {
    loginError.value = e.message
  } finally {
    loginLoading.value = false
  }
}

async function doRegister() {
  loginError.value = ''
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    loginError.value = '两次密码不一致'
    return
  }
  loginLoading.value = true
  try {
    await apiRegister(registerForm.value.username, registerForm.value.password)
    showRegister.value = false
    loginForm.value.username = registerForm.value.username
    loginForm.value.password = ''
    registerForm.value = { username: '', password: '', confirmPassword: '' }
    loginError.value = ''
    alert('注册成功，请登录')
  } catch (e) {
    loginError.value = e.message
  } finally {
    loginLoading.value = false
  }
}

function doLogout() {
  stopAudioPlayback()
  clearToken()
  isLoggedIn.value = false
  isBound.value = false
  messages.value = []
  chatHistory.length = 0
}

function stopAudioPlayback() {
  if (currentAudio.value) {
    currentAudio.value.pause()
    currentAudio.value = null
  }
  if (currentAudioUrl.value) {
    URL.revokeObjectURL(currentAudioUrl.value)
    currentAudioUrl.value = ''
  }
}

function clearTtsQueue() {
  ttsSegmentBuffer.value = ''
  ttsTextQueue.value = []
}

function splitTtsSegments(input) {
  const text = input || ''
  const segments = []
  const regex = /([。！？!?；;，,、：:\n])/
  const forceChunkSize = 36
  let rest = text
  while (true) {
    // Force-cut long text to reduce first-audio latency.
    if (rest.length >= forceChunkSize) {
      const windowText = rest.slice(0, forceChunkSize)
      const punctMatches = [...windowText.matchAll(/[。！？!?；;，,、：:]/g)]
      if (punctMatches.length > 0) {
        const last = punctMatches[punctMatches.length - 1]
        const cut = (last.index ?? 0) + last[0].length
        const seg = rest.slice(0, cut).trim()
        if (seg) segments.push(seg)
        rest = rest.slice(cut)
        continue
      }
      const seg = rest.slice(0, forceChunkSize).trim()
      if (seg) segments.push(seg)
      rest = rest.slice(forceChunkSize)
      continue
    }

    const match = rest.match(regex)
    if (!match || match.index == null) break
    const cut = match.index + match[0].length
    const seg = rest.slice(0, cut).trim()
    if (seg) segments.push(seg)
    rest = rest.slice(cut)
  }
  return { segments, rest }
}

function enqueueTtsText(text) {
  const content = (text || '').trim()
  if (!content) return
  ttsTextQueue.value.push(content)
  void drainTtsQueue()
}

async function playBlob(blob) {
  return new Promise((resolve, reject) => {
    const audioUrl = URL.createObjectURL(blob)
    const audio = new Audio(audioUrl)
    audio.playbackRate = ttsPlaybackRate.value
    currentAudio.value = audio
    currentAudioUrl.value = audioUrl

    audio.onended = () => {
      URL.revokeObjectURL(audioUrl)
      if (currentAudioUrl.value === audioUrl) currentAudioUrl.value = ''
      if (currentAudio.value === audio) currentAudio.value = null
      resolve()
    }
    audio.onerror = () => {
      URL.revokeObjectURL(audioUrl)
      if (currentAudioUrl.value === audioUrl) currentAudioUrl.value = ''
      if (currentAudio.value === audio) currentAudio.value = null
      reject(new Error('audio playback failed'))
    }
    audio.play().catch((err) => {
      URL.revokeObjectURL(audioUrl)
      if (currentAudioUrl.value === audioUrl) currentAudioUrl.value = ''
      if (currentAudio.value === audio) currentAudio.value = null
      reject(err)
    })
  })
}

async function drainTtsQueue() {
  if (!voiceMode.value || ttsQueueRunning.value) return
  ttsQueueRunning.value = true

  try {
    while (voiceMode.value && ttsTextQueue.value.length > 0) {
      const nextText = ttsTextQueue.value.shift()
      if (!nextText) continue
      const blob = await apiPostBlob('/api/agent/tts', { text: nextText })
      await playBlob(blob)
    }
  } catch (e) {
    console.error('TTS playback failed:', e)
  } finally {
    ttsQueueRunning.value = false
  }
}

async function checkBindStatus() {
  try {
    const data = await apiGet('/api/agent/bind-status')
    if (data.success && data.bound) {
      isBound.value = true
      loadGreeting()
    } else {
      isBound.value = false
    }
  } catch (e) {
    isBound.value = false
  }
}

function startBind() {
  // 直接页面跳转到 Tesla 授权（手机端兼容）
  const token = getToken()
  window.location.href = `/tesla/login-redirect?token=${encodeURIComponent(token)}`
}

function getUserLocation() {
  if (!navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userLocation.value = {
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
      }
    },
    () => { /* 用户拒绝定位，忽略 */ },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

async function loadGreeting() {
  loading.value = true
  try {
    // 先加载历史记录
    const histData = await apiGet('/api/agent/history')
    if (histData.success && histData.messages.length > 0) {
      for (const msg of histData.messages) {
        messages.value.push({ role: msg.role, content: msg.content })
      }
      // 把历史记录同步到 chatHistory 供 LLM 上下文使用
      chatHistory.push(...histData.messages)
    }

    const data = await apiGet('/api/agent/greeting')
    if (data.success) {
      vin.value = data.vin
      const statusText = formatStatus(data.vehicle_status)
      messages.value.push({
        role: 'assistant',
        content: `你好！以下是你的车辆当前状态：\n\n${statusText}\n\n有什么可以帮你的？`,
      })
      scrollToBottom()
    } else {
      messages.value.push({ role: 'assistant', content: `连接失败: ${data.error || '未知错误'}` })
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `无法连接到车辆服务: ${e.message}` })
  } finally {
    loading.value = false
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return

  input.value = ''
  sending.value = true
  stopAudioPlayback()
  clearTtsQueue()

  messages.value.push({ role: 'user', content: text })
  chatHistory.push({ role: 'user', content: text })
  scrollToBottom()

  const assistantIdx = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })
  scrollToBottom()

  try {
    await fetchEventSource(
      '/api/agent/chat',
      { messages: chatHistory, vin: vin.value, user_location: userLocation.value },
      (payload) => {
        if (payload.type === 'content') {
          messages.value[assistantIdx].content += payload.content
          if (voiceMode.value) {
            ttsSegmentBuffer.value += payload.content || ''
            const { segments, rest } = splitTtsSegments(ttsSegmentBuffer.value)
            ttsSegmentBuffer.value = rest
            for (const seg of segments) enqueueTtsText(seg)
          }
          scrollToBottom()
        } else if (payload.type === 'tool_call') {
          const toolNames = {
            get_vehicle_status: '正在查询车辆状态...',
            lock_doors: '正在锁车...',
            unlock_doors: '正在解锁...',
            actuate_trunk: '正在操作后备箱...',
          }
          messages.value[assistantIdx].toolCall = toolNames[payload.name] || `执行 ${payload.name}...`
          scrollToBottom()
        } else if (payload.type === 'done') {
          delete messages.value[assistantIdx].toolCall
          if (voiceMode.value) {
            const tail = (ttsSegmentBuffer.value || '').trim()
            if (tail) enqueueTtsText(tail)
            ttsSegmentBuffer.value = ''
          }
          scrollToBottom()
        }
      }
    )
    chatHistory.push({ role: 'assistant', content: messages.value[assistantIdx].content })
  } catch (e) {
    messages.value[assistantIdx].content = `出错了: ${e.message}`
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  // 处理 Tesla 授权回调
  const params = new URLSearchParams(window.location.search)
  const authSuccess = params.get('auth_success')
  const authError = params.get('auth_error')

  if (authSuccess || authError) {
    // 清除 URL 上的 query 参数
    window.history.replaceState({}, '', '/')
  }

  if (getToken()) {
    isLoggedIn.value = true
    getUserLocation()
    if (authSuccess) {
      // 授权成功，直接检查绑定状态
      isBound.value = true
      loadGreeting()
    } else if (authError) {
      isBound.value = false
      bindError.value = `授权失败: ${authError}`
    } else {
      checkBindStatus()
    }
  }
})
</script>
