// 分类常量（前端共用）——与后端 contents.type 一一对应
// value 存库；label 展示文案；tagType 用于 Element Plus 标签颜色
export const TYPE_MAP = {
  activity: { label: '校园活动', tagType: 'success' },
  meeting: { label: '校园会议', tagType: 'warning' },
  news: { label: '校园动态', tagType: 'info' },
  ad: { label: '校园广告', tagType: 'danger' }
}

// 广告的二级子分类（后续可扩展）
export const AD_CATEGORIES = ['闲置', '求助', '宣传']

export const TYPE_LIST = Object.entries(TYPE_MAP).map(([value, item]) => ({
  value,
  label: item.label
}))

// 时间显示：2026-09-02T18:52:03 -> 2026-09-02 18:52
export function formatTime(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 16)
}
