<script setup>
// 右上角常驻天气小组件（归属：前端 B）
// 《新增功能规划书》三-7 天气出行提示模块：
// - 真实天气数据：Open-Meteo API（免费、无需注册、无需 key、支持浏览器直连）
// - 真实定位：浏览器 Geolocation 优先 → IP 定位回退 → 校园坐标兜底
// - 展示今日 / 明日天气与气温，并结合天气给出校园出行建议
// 挂载方式：在 MainLayout.vue 的模板中加入 <WeatherWidget />
import { onMounted, ref } from 'vue'

// 校园坐标（兜底：山东理工大学西校区·淄博 新村西路266号）
const CAMPUS = { lng: 118.001917, lat: 36.814013, name: '山东理工大学（淄博）' }

const open = ref(false) // 是否展开
const loading = ref(true)
const failed = ref(false)
const today = ref(null)
const tomorrow = ref(null)
const tip = ref('')
const cityName = ref('') // 当前定位位置名

// WMO 天气现象代码 → [文案, 图标]（Open-Meteo 使用 WMO 标准代码）
const WMO_MAP = {
  0: ['晴', '☀️'], 1: ['基本晴', '🌤️'], 2: ['多云', '⛅'], 3: ['阴', '☁️'],
  45: ['雾', '🌫️'], 48: ['雾凇', '🌫️'],
  51: ['小毛毛雨', '🌦️'], 53: ['毛毛雨', '🌦️'], 55: ['大毛毛雨', '🌧️'],
  61: ['小雨', '🌦️'], 63: ['中雨', '🌧️'], 65: ['大雨', '🌧️'],
  66: ['冻雨', '🌧️'], 67: ['强冻雨', '🌧️'],
  71: ['小雪', '🌨️'], 73: ['中雪', '🌨️'], 75: ['大雪', '❄️'], 77: ['雪粒', '🌨️'],
  80: ['阵雨', '🌦️'], 81: ['阵雨', '🌧️'], 82: ['强阵雨', '⛈️'],
  85: ['阵雪', '🌨️'], 86: ['阵雪', '❄️'],
  95: ['雷阵雨', '⛈️'], 96: ['雷雨伴冰雹', '⛈️'], 99: ['雷雨伴冰雹', '⛈️']
}

function describe(code) {
  return WMO_MAP[code] || ['未知', '🌡️']
}

// 结合今日天气生成出行建议（规划书要求，无强制弹窗）
function buildTip(d) {
  if ([51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99].includes(d.code)) {
    return '今天有雨，出门记得带伞 ☂️'
  }
  if (d.tMax >= 32) return '今天高温，注意防晒、多补水 🧴'
  if (d.tMin <= 5) return '今天降温，记得添件外套 🧥'
  if ([45, 48].includes(d.code)) return '今天有雾，出行注意交通安全 🚶'
  return '天气不错，适合出门活动 🎉'
}

// ---------- 定位（三级回退） ----------

// ① 浏览器 Geolocation（精确，需要用户授权）
function locateByGeolocation(timeoutMs = 6000) {
  return new Promise((resolve) => {
    if (!('geolocation' in navigator)) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(null),
      { timeout: timeoutMs, maximumAge: 10 * 60 * 1000 }
    )
  })
}

// ② IP 定位（免费、无需授权，返回城市名+坐标）
async function locateByIp() {
  try {
    const res = await fetch('https://get.geojs.io/v1/ip/geo.json', { signal: AbortSignal.timeout(6000) })
    const json = await res.json()
    const lat = parseFloat(json.latitude)
    const lng = parseFloat(json.longitude)
    if (Number.isFinite(lat) && Number.isFinite(lng) && lat !== 0 && lng !== 0) {
      const city = json.city || json.region || ''
      return { lat, lng, name: city ? `${city}` : '' }
    }
    return null
  } catch {
    return null
  }
}

// 综合定位：Geolocation → IP → 校园兜底
async function getLocation() {
  const geo = await locateByGeolocation()
  if (geo) {
    // 拿到精确坐标后，再用 IP 定位补充城市名（大概率同城，失败则显示"当前位置"）
    const ip = await locateByIp().catch(() => null)
    cityName.value = ip?.name || '当前位置'
    return geo
  }
  const ip = await locateByIp()
  if (ip) {
    cityName.value = ip.name || '当前位置'
    return ip
  }
  cityName.value = CAMPUS.name
  return { lat: CAMPUS.lat, lng: CAMPUS.lng }
}

// ---------- 天气 ----------

// 天气接口走 fetch 直连外部 API，不经过 /api 代理与 axios 封装
async function loadWeather() {
  loading.value = true
  failed.value = false
  try {
    const loc = await getLocation()
    const url =
      'https://api.open-meteo.com/v1/forecast' +
      `?latitude=${loc.lat}&longitude=${loc.lng}` +
      '&daily=weather_code,temperature_2m_max,temperature_2m_min' +
      '&timezone=auto&forecast_days=2'
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) })
    const json = await res.json()
    const daily = json.daily
    if (!daily) throw new Error('empty')
    const build = (i) => ({
      date: daily.time[i],
      code: daily.weather_code[i],
      tMax: Math.round(daily.temperature_2m_max[i]),
      tMin: Math.round(daily.temperature_2m_min[i])
    })
    today.value = build(0)
    tomorrow.value = build(1)
    tip.value = buildTip(today.value)
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

onMounted(loadWeather)
</script>

<template>
  <div class="weather-widget">
    <!-- 收起态：右上角小图标条，点击展开 -->
    <div v-if="!open" class="mini" title="点击查看天气与出行建议" @click="open = true">
      <template v-if="!loading && !failed">
        <span class="mini-icon">{{ describe(today.code)[1] }}</span>
        <span class="mini-temp">{{ today.tMin }}~{{ today.tMax }}℃</span>
      </template>
      <span v-else-if="!loading" class="mini-icon">☁️</span>
      <span v-else class="mini-temp">…</span>
    </div>

    <!-- 展开态：今日 / 明日天气 + 出行建议 -->
    <div v-else class="panel">
      <div class="panel-head">
        <b>{{ cityName || '当前' }}天气</b>
        <el-button text size="small" @click="open = false">收起</el-button>
      </div>

      <div v-if="loading" class="state">天气加载中…</div>
      <div v-else-if="failed" class="state">
        天气获取失败
        <el-button text size="small" type="primary" @click="loadWeather">重试</el-button>
      </div>
      <template v-else>
        <div v-for="(d, i) in [today, tomorrow]" :key="d.date" class="row">
          <span class="day">{{ i === 0 ? '今天' : '明天' }}</span>
          <span class="icon">{{ describe(d.code)[1] }}</span>
          <span class="text">{{ describe(d.code)[0] }}</span>
          <span class="temp">{{ d.tMin }}~{{ d.tMax }}℃</span>
        </div>
        <div class="tip">{{ tip }}</div>
        <div class="loc-tip">📍 {{ cityName || '当前位置' }}</div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.weather-widget {
  position: fixed;
  top: 64px; /* 顶部导航栏下方 */
  right: 16px;
  z-index: 2000;
}

.mini {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  user-select: none;
}

.mini-icon {
  font-size: 16px;
}

.mini-temp {
  font-size: 12px;
  color: #606266;
}

.panel {
  width: 230px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 10px 14px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  color: #303133;
  font-size: 14px;
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
  color: #909399;
}

.icon {
  font-size: 18px;
}

.temp {
  margin-left: auto;
  color: #303133;
}

.tip {
  margin-top: 8px;
  padding: 8px 10px;
  background: #f0f7ff;
  border-radius: 8px;
  color: #1d6df0;
  font-size: 12px;
  line-height: 1.6;
}

.state {
  padding: 10px 0;
  color: #909399;
  font-size: 13px;
  text-align: center;
}

.loc-tip {
  margin-top: 6px;
  color: #909399;
  font-size: 11px;
  text-align: right;
}
</style>
