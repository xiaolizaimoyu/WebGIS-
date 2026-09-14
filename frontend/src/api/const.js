// 分类常量（前端共用）——与后端 contents.type 一一对应
// value 存库；label 展示文案；tagType 用于 Element Plus 标签颜色；mapColor 用于地图点位颜色
export const TYPE_MAP = {
  meeting: { label: '校园会议', tagType: 'warning', mapColor: '#f59f00' },
  news: { label: '校园动态', tagType: 'info', mapColor: '#1971c2' },
  food: { label: '美食分享', tagType: 'primary', mapColor: '#f06595' },
  lost: { label: '失物招领', tagType: 'warning', mapColor: '#6741d9' }
}

// 地图配置（高德 JS API 2.0，坐标 GCJ-02 火星坐标系）。
// center 为山东理工大学西校区（淄博·新村西路 266 号），与后端 seed.py 的 MAP_CENTER 保持一致。
export const MAP_CONFIG = {
  center: [36.814398, 118.007853], // [lat, lng] 兼容旧顺序
  zoom: 16,
  maxZoom: 18
}

// 校园中心（OpenLayers 组件 [lng, lat] 顺序；发布页/列表页共用，避免各页面写死北京/广州坐标）
export const CAMPUS_CENTER = { lng: 118.001917, lat: 36.814013, name: '山东理工大学（淄博）' }

// 校园地点库（山东理工大学西校区·淄博）：发帖选点、列表页地图参考点
// 坐标在校园中心（118.001917, 36.814013）周边按真实方位分布（约 0.0009°/100m）
export const CAMPUS_PLACES = [
  { name: '北门（新村西路）', lng: 118.006732, lat: 36.816583 },
  { name: '图书馆', lng: 118.006431, lat: 36.815182 },
  { name: '鸿远楼（行政楼）', lng: 118.007535, lat: 36.814284 },
  { name: '一号教学楼', lng: 118.008939, lat: 36.81599 },
  { name: '二号教学楼', lng: 118.007836, lat: 36.815786 },
  { name: '三号教学楼', lng: 118.005829, lat: 36.813579 },
  { name: '逸夫楼', lng: 118.006331, lat: 36.81268 },
  { name: '第一食堂（一餐）', lng: 118.010043, lat: 36.815693 },
  { name: '第二食堂（二餐）', lng: 118.009541, lat: 36.81309 },
  { name: '第三食堂（三餐）', lng: 118.005528, lat: 36.815479 },
  { name: '体育馆', lng: 118.011146, lat: 36.813595 },
  { name: '田径场', lng: 118.010344, lat: 36.814493 },
  { name: '学生公寓区', lng: 118.008137, lat: 36.816988 },
  { name: '大学生事务中心', lng: 118.006832, lat: 36.814182 },
  { name: '校医院', lng: 118.005027, lat: 36.814677 },
  { name: '东门', lng: 118.012752, lat: 36.8144 },
  { name: '南门', lng: 118.007835, lat: 36.812584 }
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
