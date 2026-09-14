// 地图内核工具（高德 JS API 2.0 版）
// 说明：本文件 + components/map/ 下两个组件是“对地图库唯一依赖”的地方。
//       坐标统一为 GCJ-02（高德火星坐标），与瓦片/定位全链路一致。
import { loadAMap } from './amap-loader'
import { CAMPUS_CENTER, TYPE_MAP } from '@/api/const'

// 兼容导出（高德版不再使用 tileUrl，保留对象避免破坏旧引用）
export const MAP_CONFIG = {
  center: [CAMPUS_CENTER.lat, CAMPUS_CENTER.lng],
  zoom: 16,
  maxZoom: 18
}

// 分类 -> 颜色/文案
export const colorOf = (type) => TYPE_MAP[type]?.mapColor || '#8a8f98'
export const labelOf = (type) => TYPE_MAP[type]?.label || type || '未知'

// 初始化高德地图（异步，需 await）
export async function initMap(containerEl, cfg = {}) {
  const AMap = await loadAMap()
  const map = new AMap.Map(containerEl, {
    center: cfg.center || [CAMPUS_CENTER.lng, CAMPUS_CENTER.lat],
    zoom: cfg.zoom || 16,
    mapStyle: 'amap://styles/normal'
  })
  return map
}

// 用 DOM 节点拼接弹窗内容（防 XSS：一律 textContent，不用 v-html）
export function buildPopupEl(item, onDetail) {
  const wrap = document.createElement('div')
  wrap.style.minWidth = '210px'
  wrap.style.maxWidth = '260px'

  const head = document.createElement('div')
  head.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:6px'
  const tag = document.createElement('span')
  tag.textContent = labelOf(item.type)
  tag.style.cssText =
    'font-size:11px;color:#fff;background:' + colorOf(item.type) + ';padding:1px 8px;border-radius:10px'
  const title = document.createElement('div')
  title.textContent = item.title || ''
  title.style.cssText = 'font-size:14px;font-weight:600;color:#303133;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'
  head.appendChild(tag)
  head.appendChild(title)

  const meta = document.createElement('div')
  meta.style.cssText = 'font-size:12px;color:#909399;margin-bottom:6px'
  meta.textContent = [item.author_name, item.created_at].filter(Boolean).join(' · ')

  const body = document.createElement('div')
  body.style.cssText = 'font-size:12px;color:#606266;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden'
  body.textContent = item.body || ''

  const btn = document.createElement('div')
  btn.textContent = '查看详情 →'
  btn.style.cssText =
    'font-size:12px;color:#1d6df0;cursor:pointer;text-align:right;padding-top:4px;border-top:1px solid #f0f0f0'
  btn.onclick = () => onDetail && onDetail(item.id)

  wrap.appendChild(head)
  wrap.appendChild(meta)
  wrap.appendChild(body)
  wrap.appendChild(btn)
  return wrap
}
