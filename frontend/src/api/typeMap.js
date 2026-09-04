// 内容分类常量扩展（归属：前端 B）
// 《新增功能规划书》5-2：B 负责新增「美食分享 / 失物招领」两个业务分类。
// 公共 const.js 归前端 C 所有，按协作铁律不改他人文件，
// 故在此基于公共 TYPE_MAP 做纯扩展，B 的四个页面统一从这里取 TYPE_MAP。
// 前端 C 后续把 food/lost 合入 const.js 后，本文件可整体删除。
import { TYPE_MAP as BASE_TYPE_MAP } from './const'

export const TYPE_MAP = {
  ...BASE_TYPE_MAP,
  // 美食分享：主题蓝标签；失物招领：橙色标签更醒目
  food: { label: '美食分享', tagType: 'primary' },
  lost: { label: '失物招领', tagType: 'warning' }
}
