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

// 校园中心（OpenLayers 组件 [lng, lat] 顺序；发布页/列表页共用，避免各页面写死北京/广州坐标）
export const CAMPUS_CENTER = { lng: 118.001917, lat: 36.814013, name: '山东理工大学（淄博）' }

// 校园地点库（山东理工大学西校区·淄博）：发帖选点、列表页地图参考点
// 坐标在校园中心（118.001917, 36.814013）周边按真实方位分布（约 0.0009°/100m）
export const CAMPUS_PLACES = [
  { name: '北门（新村西路）', lng: 118.0008, lat: 36.8162 },
  { name: '图书馆', lng: 118.0005, lat: 36.8148 },
  { name: '鸿远楼（行政楼）', lng: 118.0016, lat: 36.8139 },
  { name: '一号教学楼', lng: 118.0030, lat: 36.8156 },
  { name: '二号教学楼', lng: 118.0019, lat: 36.8154 },
  { name: '三号教学楼', lng: 117.9999, lat: 36.8132 },
  { name: '逸夫楼', lng: 118.0004, lat: 36.8123 },
  { name: '第一食堂（一餐）', lng: 118.0041, lat: 36.8153 },
  { name: '第二食堂（二餐）', lng: 118.0036, lat: 36.8127 },
  { name: '第三食堂（三餐）', lng: 117.9996, lat: 36.8151 },
  { name: '体育馆', lng: 118.0052, lat: 36.8132 },
  { name: '田径场', lng: 118.0044, lat: 36.8141 },
  { name: '学生公寓区', lng: 118.0022, lat: 36.8166 },
  { name: '大学生事务中心', lng: 118.0009, lat: 36.8138 },
  { name: '校医院', lng: 117.9991, lat: 36.8143 },
  { name: '东门', lng: 118.0068, lat: 36.8140 },
  { name: '南门', lng: 118.0019, lat: 36.8122 }
]

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
