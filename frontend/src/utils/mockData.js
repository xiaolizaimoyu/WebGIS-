// 模拟数据（归属：前端 C 调试用）——后端未启动时的兜底数据
// 注意：此文件仅用于前端独立开发调试，不参与后端联调
export function getMockContents() {
  const now = Date.now()
  const day = 86400000
  return [
    {
      id: 1, title: '篮球友谊赛报名中', body: '本周六下午3点，校体育馆篮球场，欢迎各位篮球爱好者踊跃报名参加！',
      type: 'activity', category: '体育', author_name: '体育部', created_at: now - 1 * day,
      lng: 116.397428, lat: 39.90923, images: []
    },
    {
      id: 2, title: '校园歌手大赛海选', body: '一年一度的校园歌手大赛开始啦，报名截止本周五，快来展现你的歌喉！',
      type: 'activity', category: '文艺', author_name: '文艺部', created_at: now - 2 * day,
      lng: 116.407428, lat: 39.91923, images: []
    },
    {
      id: 3, title: '招聘暑期实习', body: '互联网公司暑期实习招聘，前端/后端/产品多岗位，欢迎投递简历。',
      type: 'news', category: '招聘', author_name: '就业办', created_at: now - 3 * day,
      lng: 116.387428, lat: 39.89923, images: []
    },
    {
      id: 4, title: '图书馆延长开放通知', body: '期末考试将至，图书馆开放时间延长至晚11点，请同学们合理安排复习时间。',
      type: 'news', category: '通知', author_name: '图书馆', created_at: now - 4 * day,
      lng: 116.392428, lat: 39.90423, images: []
    }
  ]
}
