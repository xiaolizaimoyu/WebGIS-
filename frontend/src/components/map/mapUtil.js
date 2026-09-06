// 地图内核工具（归属：前端 A）
// 说明：本文件 + components/map/ 下两个组件是“对地图库唯一有依赖”的地方。
//       将来若升级到高德 JS API，只需替换这几处内核，页面（MapView / PublishView）不用改。
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { MAP_CONFIG, TYPE_MAP } from '@/api/const'

export { MAP_CONFIG }

// 分类 -> 颜色/文案
export const colorOf = (type) => TYPE_MAP[type]?.mapColor || '#8a8f98'
export const labelOf = (type) => TYPE_MAP[type]?.label || type || '未知'

// 瓦片源说明：
// 默认高德栅格瓦片（国内加载快、中文标注）。subdomains 用 1-4。
// 如需换回 OpenStreetMap：把 const.js MAP_CONFIG 的 tileUrl 换为
//   'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'，subdomains 留空数组，attribution 填 OSM 版权。
export function initMap(containerEl, cfg = {}) {
  const map = L.map(containerEl, {
    zoomControl: false,
    attributionControl: true
  })
  L.control.zoom({ position: 'topright' }).addTo(map)
  L.tileLayer(cfg.tileUrl || MAP_CONFIG.tileUrl, {
    attribution: cfg.tileAttribution !== undefined ? cfg.tileAttribution : MAP_CONFIG.tileAttribution,
    maxZoom: cfg.maxZoom || MAP_CONFIG.maxZoom || 19,
    subdomains: cfg.subdomains || MAP_CONFIG.subdomains || []
  }).addTo(map)
  map.setView(cfg.center || MAP_CONFIG.center, cfg.zoom || MAP_CONFIG.zoom)
  return map
}

// 用 DOM 节点拼接弹窗内容（防 XSS：一律 textContent，不用 v-html）
export function buildPopupEl(item, onDetail) {
  const wrap = document.createElement('div')
  wrap.style.minWidth = '210px'
  wrap.style.maxWidth = '260px'

  const head = document.createElement('div')
  head.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:6px'
  const dot = document.createElement('span')
  dot.style.cssText = `width:10px;height:10px;border-radius:50%;background:${colorOf(item.type)};display:inline-block`
  const tag = document.createElement('span')
  tag.style.cssText = 'font-size:12px;color:#909399'
  tag.textContent = labelOf(item.type)
  head.append(dot, tag)
  wrap.append(head)

  const title = document.createElement('div')
  title.style.cssText = 'font-size:15px;font-weight:600;color:#303133;margin-bottom:4px'
  title.textContent = item.title || ''
  wrap.append(title)

  if (item.body) {
    const body = document.createElement('div')
    body.style.cssText = 'font-size:13px;color:#606266;line-height:1.5;margin-bottom:6px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical'
    body.textContent = String(item.body).slice(0, 90)
    wrap.append(body)
  }

  const meta = document.createElement('div')
  meta.style.cssText = 'font-size:12px;color:#a8abb2;margin-bottom:8px'
  meta.textContent = `${item.author_name || '匿名'} · ${String(item.created_at || '').replace('T', ' ').slice(0, 16)}`
  wrap.append(meta)

  const link = document.createElement('a')
  link.href = 'javascript:void(0)'
  link.textContent = '查看详情 →'
  link.style.cssText = 'font-size:13px;color:#1d6df0;cursor:pointer'
  link.onclick = () => onDetail(item.id)
  wrap.append(link)

  return wrap
}
