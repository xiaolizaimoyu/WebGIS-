// 模拟数据（归属：前端 C 调试用）——后端未启动时的兜底数据
// 注意：此文件仅用于前端独立开发调试，不参与后端联调
const now = Date.now()
const day = 86400000
const hour = 3600000

export function getMockContents() {
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

// ====== 校园问答 Mock ======
export function getMockQuestions() {
  return [
    {
      id: 1, title: '高数期末复习重点有哪些？', body: '马上要期末考试了，求学长学姐分享一下高数下册的复习重点和必考题型，万分感谢！',
      tag: '高数', author_name: '小学弟', author_avatar: '', created_at: now - 2 * hour,
      views: 328, answer_count: 5, adopted: true
    },
    {
      id: 2, title: '学校附近哪家外卖好吃又便宜？', body: '求推荐学校周边性价比高的外卖，预算15元以内，最好是辣的！',
      tag: '生活', author_name: '吃货同学', author_avatar: '', created_at: now - 5 * hour,
      views: 156, answer_count: 12, adopted: false
    },
    {
      id: 3, title: 'GIS专业考研选哪个方向比较好？', body: '本人地理空间信息工程专业，想考研，请问遥感、GIS开发、空间分析哪个方向就业前景更好？',
      tag: '考研', author_name: '迷茫的大三', author_avatar: '', created_at: now - 1 * day,
      views: 489, answer_count: 8, adopted: true
    },
    {
      id: 4, title: '图书馆怎么预约座位？', body: '第一次去图书馆，请问座位预约系统怎么用？需要下载什么APP吗？',
      tag: '求助', author_name: '新生小白', author_avatar: '', created_at: now - 2 * day,
      views: 89, answer_count: 3, adopted: false
    },
    {
      id: 5, title: 'Python数据分析怎么入门？', body: '零基础想学Python做数据分析，有没有推荐的学习路线和资源？',
      tag: '编程', author_name: '代码小白', author_avatar: '', created_at: now - 3 * day,
      views: 267, answer_count: 6, adopted: true
    }
  ]
}

export function getMockQuestionDetail(id) {
  const list = getMockQuestions()
  const q = list.find((x) => x.id === Number(id)) || list[0]
  return { ...q, body: q.body + '\n\n补充：希望能有具体的章节重点和题型分析。' }
}

export function getMockAnswers(questionId) {
  return [
    {
      id: 1, question_id: questionId, body: '高数下册重点：多元函数微分学、重积分、曲线积分与曲面积分、无穷级数。必考题型：偏导数计算、二重积分交换积分次序、格林公式应用、幂级数收敛域。',
      author_name: '学霸学姐', author_avatar: '', created_at: now - 1 * hour, likes: 24, adopted: true
    },
    {
      id: 2, question_id: questionId, body: '推荐看汤家凤的基础班视频，配合1800题练习，先把基础打牢。重点章节多做真题。',
      author_name: '考研上岸人', author_avatar: '', created_at: now - 3 * hour, likes: 15, adopted: false
    },
    {
      id: 3, question_id: questionId, body: '曲线积分和曲面积分是难点，一定要搞清楚格林公式、高斯公式、斯托克斯公式的使用条件和区别。',
      author_name: '数学达人', author_avatar: '', created_at: now - 6 * hour, likes: 8, adopted: false
    }
  ]
}

// ====== 学习资料 Mock ======
export function getMockMaterials() {
  return [
    {
      id: 1, title: '高等数学（下册）期末复习笔记.pdf', description: '整理了高数下册所有重点公式、定理和典型例题，共45页，适合考前突击。',
      subject: '数学', file_type: 'pdf', file_size: '2.3 MB', downloads: 342, likes: 56,
      author_name: '学霸笔记', author_avatar: '', created_at: now - 1 * day, tags: ['高数', '期末', '复习']
    },
    {
      id: 2, title: 'GIS原理与应用课件完整版.zip', description: '地理信息系统原理课程全部PPT课件，含12章内容，配套实验指导书。',
      subject: 'GIS', file_type: 'zip', file_size: '15.6 MB', downloads: 189, likes: 34,
      author_name: '课代表', author_avatar: '', created_at: now - 2 * day, tags: ['GIS', '课件', '专业课']
    },
    {
      id: 3, title: 'Python数据分析实战教程.docx', description: '从零基础到实战的Python数据分析教程，含pandas、numpy、matplotlib完整示例代码。',
      subject: '编程', file_type: 'docx', file_size: '5.1 MB', downloads: 567, likes: 128,
      author_name: '代码达人', author_avatar: '', created_at: now - 3 * day, tags: ['Python', '数据分析', '编程']
    },
    {
      id: 4, title: '大学英语四级真题+答案解析（2020-2025）.pdf', description: '近五年英语四级真题及详细答案解析，含听力原文和作文范文。',
      subject: '英语', file_type: 'pdf', file_size: '8.9 MB', downloads: 892, likes: 203,
      author_name: '英语学霸', author_avatar: '', created_at: now - 5 * day, tags: ['四级', '英语', '真题']
    },
    {
      id: 5, title: '遥感图像处理ENVI实验指导.pdf', description: 'ENVI 5.3 遥感图像处理实验指导，含辐射定标、大气校正、NDVI计算、分类等完整流程。',
      subject: '遥感', file_type: 'pdf', file_size: '12.4 MB', downloads: 156, likes: 41,
      author_name: '遥感学长', author_avatar: '', created_at: now - 1 * day, tags: ['遥感', 'ENVI', '实验']
    }
  ]
}

export function getMockMaterialDetail(id) {
  const list = getMockMaterials()
  return list.find((x) => x.id === Number(id)) || list[0]
}

// ====== 组队拼车 Mock ======
export function getMockCarpools() {
  return [
    {
      id: 1, title: '周末去泰山拼车', from: '学校南门', to: '泰山风景区', depart_time: '2026-09-06 06:00',
      return_time: '2026-09-07 18:00', seats_total: 4, seats_left: 2, price_per_person: 80,
      author_name: '旅行达人', author_avatar: '', phone: '138****8888', note: '已有2人报名，还差2人，费用AA，含油费过路费。',
      created_at: now - 2 * hour, status: 'recruiting'
    },
    {
      id: 2, title: '国庆回家拼车（济南方向）', from: '学校东门', to: '济南火车站', depart_time: '2026-09-30 14:00',
      return_time: '', seats_total: 3, seats_left: 1, price_per_person: 120,
      author_name: '济南老乡', author_avatar: '', phone: '139****9999', note: '私家车，空间大，可放行李，只拼女生优先。',
      created_at: now - 1 * day, status: 'recruiting'
    },
    {
      id: 3, title: '去高铁站拼车（随时出发）', from: '学校北门', to: '北京南站', depart_time: '2026-09-05 15:00',
      return_time: '', seats_total: 4, seats_left: 3, price_per_person: 50,
      author_name: '顺风车', author_avatar: '', phone: '137****7777', note: '今天下午3点出发，赶高铁的同学速来！',
      created_at: now - 30 * 60000, status: 'recruiting'
    }
  ]
}

export function getMockCarpoolDetail(id) {
  const list = getMockCarpools()
  return list.find((x) => x.id === Number(id)) || list[0]
}

// ====== 失物招领 Mock ======
export function getMockLostFound() {
  return [
    {
      id: 1, type: 'lost', title: '丢失黑色钱包', item_name: '黑色皮质钱包', location: '图书馆三楼自习室',
      lost_time: '2026-09-04 15:30', contact: '138****1234', description: '内有身份证、校园卡和少量现金，身份证姓名为张三，有重要证件，望拾到者联系，必有重谢！',
      author_name: '失主小张', author_avatar: '', images: [], created_at: now - 1 * day, status: 'open'
    },
    {
      id: 2, type: 'found', title: '捡到一串钥匙', item_name: '银色钥匙串（带小熊挂件）', location: '一食堂门口',
      lost_time: '2026-09-05 12:00', contact: '微信：abc123', description: '今天中午在一食堂门口捡到一串钥匙，上面有个棕色小熊挂件，失主请联系我认领。',
      author_name: '好心人', author_avatar: '', images: [], created_at: now - 2 * hour, status: 'open'
    },
    {
      id: 3, type: 'lost', title: '丢失AirPods Pro', item_name: '白色AirPods Pro耳机盒', location: '操场跑道',
      lost_time: '2026-09-03 18:00', contact: 'QQ：567890', description: '周三晚上跑步时丢失，耳机盒上有贴纸标记，里面有一对耳机，找到的同学请联系，感谢！',
      author_name: '运动达人', author_avatar: '', images: [], created_at: now - 2 * day, status: 'open'
    }
  ]
}

// ====== 通知 Mock ======
export function getMockNotifications() {
  return [
    {
      id: 1, type: 'comment', title: '新评论', content: '学霸学姐 评论了你的问题「高数期末复习重点有哪些？」',
      related_id: 1, related_type: 'question', read: false, created_at: now - 10 * 60000
    },
    {
      id: 2, type: 'like', title: '新点赞', content: '考研上岸人 点赞了你的回答',
      related_id: 1, related_type: 'answer', read: false, created_at: now - 30 * 60000
    },
    {
      id: 3, type: 'answer', title: '新回答', content: '数学达人 回答了你的问题「Python数据分析怎么入门？」',
      related_id: 5, related_type: 'question', read: false, created_at: now - 2 * hour
    },
    {
      id: 4, type: 'system', title: '系统通知', content: '您的资料「GIS原理与应用课件完整版.zip」已通过审核，感谢分享！',
      related_id: null, related_type: 'system', read: true, created_at: now - 1 * day
    },
    {
      id: 5, type: 'carpool', title: '拼车申请', content: '旅行达人 同意了你的拼车申请「周末去泰山拼车」',
      related_id: 1, related_type: 'carpool', read: true, created_at: now - 2 * day
    },
    {
      id: 6, type: 'sign', title: '签到提醒', content: '您已连续签到7天，获得额外奖励积分20分！',
      related_id: null, related_type: 'system', read: true, created_at: now - 3 * day
    }
  ]
}

// ====== 签到 Mock ======
export function getMockSignStatus() {
  return {
    signedToday: false,
    continuousDays: 7,
    totalPoints: 368,
    signRecords: [
      { date: '2026-09-04', points: 10 },
      { date: '2026-09-03', points: 10 },
      { date: '2026-09-02', points: 10 },
      { date: '2026-09-01', points: 10 },
      { date: '2026-08-31', points: 10 },
      { date: '2026-08-30', points: 10 },
      { date: '2026-08-29', points: 20 }
    ]
  }
}

// ====== 用户 Mock ======
export function getMockUserProfile(id) {
  return {
    id: Number(id) || 1,
    nickname: id === '1' ? '校园达人' : '热心同学',
    avatar: '',
    bio: '热爱生活，热爱学习，GIS专业大三学生一枚～',
    gender: '男',
    major: '地理空间信息工程',
    grade: '大三',
    post_count: 23,
    follower_count: 156,
    following_count: 89,
    likes_received: 432,
    created_at: now - 180 * day
  }
}

export function getMockUserPosts(userId) {
  return getMockContents().slice(0, 3).map((c) => ({ ...c, author_id: userId }))
}

export function getMockFollowers(userId) {
  return [
    { id: 10, nickname: '粉丝A', avatar: '', bio: '关注中' },
    { id: 11, nickname: '粉丝B', avatar: '', bio: '' },
    { id: 12, nickname: '粉丝C', avatar: '', bio: 'GIS爱好者' }
  ]
}

export function getMockFollowing(userId) {
  return [
    { id: 20, nickname: '关注A', avatar: '', bio: '' },
    { id: 21, nickname: '关注B', avatar: '', bio: '学霸' }
  ]
}

// ====== 我的报名 Mock ======
export function getMockMyApplications() {
  return [
    { id: 1, carpool_id: 1, title: '周末去泰山拼车', status: 'approved', apply_time: now - 1 * day },
    { id: 2, carpool_id: 2, title: '国庆回家拼车（济南方向）', status: 'pending', apply_time: now - 2 * hour }
  ]
}
