// 分类常量（前端共用）——与后端 contents.type 一一对应
// value 存库；label 展示文案；tagType 用于 Element Plus 标签颜色；mapColor 用于地图点位颜色
export const TYPE_MAP = {
  meeting: { label: '校园会议', tagType: 'warning', mapColor: '#f59f00' },
  news: { label: '校园动态', tagType: 'info', mapColor: '#1971c2' },
  food: { label: '美食分享', tagType: 'primary', mapColor: '#f06595' },
  lost: { label: '失物招领', tagType: 'warning', mapColor: '#6741d9' }
}

// 地图配置（Leaflet，无需 key）。
// center 为山东理工大学西校区（淄博·新村西路 266 号），与后端 seed.py 的 MAP_CENTER 保持一致。
// 瓦片默认用高德栅格瓦片（国内加载快、中文标注）；如需换回 OSM 请看 mapUtil.js 里的注释。
export const MAP_CONFIG = {
  center: [36.814013, 118.001917], // [lat, lng]（Leaflet 纬度在前）
  zoom: 16,
  tileUrl: 'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
  tileAttribution: '',
  subdomains: ['1', '2', '3', '4'],
  maxZoom: 18
}

export const TYPE_LIST = Object.entries(TYPE_MAP).map(([value, item]) => ({
  value,
  label: item.label
}))

// 时间显示：支持 ISO 字符串（2026-09-02T18:52:03）和数字时间戳
export function formatTime(value) {
  if (!value) return ''
  // 数字时间戳转换为 ISO 格式
  const str = typeof value === 'number' ? new Date(value).toISOString() : String(value)
  return str.replace('T', ' ').slice(0, 16)
}
