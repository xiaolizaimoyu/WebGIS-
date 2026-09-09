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
      lng: 118.0005, lat: 36.8148, images: []
    },
    {
      id: 2, title: '校园歌手大赛海选', body: '一年一度的校园歌手大赛开始啦，报名截止本周五，快来展现你的歌喉！',
      type: 'activity', category: '文艺', author_name: '文艺部', created_at: now - 2 * day,
      lng: 118.0036, lat: 36.8127, images: []
    },
    {
      id: 3, title: '招聘暑期实习', body: '互联网公司暑期实习招聘，前端/后端/产品多岗位，欢迎投递简历。',
      type: 'news', category: '招聘', author_name: '就业办', created_at: now - 3 * day,
      lng: 118.0041, lat: 36.8153, images: []
    },
    {
      id: 4, title: '图书馆延长开放通知', body: '期末考试将至，图书馆开放时间延长至晚11点，请同学们合理安排复习时间。',
      type: 'news', category: '通知', author_name: '图书馆', created_at: now - 4 * day,
      lng: 118.0052, lat: 36.8132, images: []
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

// ====== 积分商城 Mock ======
const mallImageUrls = [
  // 本地真实商品图（backend/uploads/mall/，由 vite 代理 /uploads 到后端）
  // 按 mock 商品主题分配：笔记本/马克杯/学习资料(图书馆)/白色织品/数码
  '/mall/goods_1.jpg', // 1 校园定制笔记本
  '/mall/goods_2.jpg', // 2 定制马克杯
  '/mall/goods_4.jpg', // 3 高数押题卷-图书馆学习场景
  '/mall/goods_5.jpg', // 4 校园帆布袋-白色织品
  '/mall/goods_4.jpg', // 5 四级词汇手册-图书馆
  '/mall/goods_6.jpg', // 6 定制U盘-数码
  '/mall/goods_4.jpg', // 7 占座神器-图书馆
  '/mall/goods_4.jpg', // 8 考研思维导图-图书馆
  '/mall/goods_2.jpg', // 9 运动水壶-杯具
  '/mall/goods_6.jpg', // 10 蓝牙耳机
  '/mall/goods_4.jpg', // 11 GIS实验指导书-图书馆
  '/mall/goods_5.jpg'  // 12 定制抱枕-白色软织品
]

export function getMockGoods() {
  return [
    {
      id: 1,
      name: '校园定制笔记本',
      description: '校园专属定制精装笔记本，采用优质道林纸，书写顺滑不洇墨。封面烫金校徽，质感十足，是上课记笔记、写日记、做手账的绝佳选择。',
      category: '文具',
      points: 100,
      stock: 50,
      sold: 128,
      image: mallImageUrls[0],

      imageBg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      tags: ['热门', '新品'],
      features: ['优质道林纸100页', '封面烫金校徽', 'A5便携尺寸', '附赠书签带'],
      specs: '尺寸：A5 (148×210mm) | 页数：100张 | 封面：PU皮烫金'
    },
    {
      id: 2,
      name: '定制陶瓷马克杯',
      description: '校园定制陶瓷马克杯，采用景德镇优质高岭土烧制，杯身浮雕校徽，手感温润。350ml大容量，可微波炉加热、洗碗机清洗，附赠精美礼盒包装。',
      category: '生活用品',
      points: 200,
      stock: 30,
      sold: 86,
      image: mallImageUrls[1],

      imageBg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      tags: ['热门'],
      features: ['景德镇高岭土烧制', '杯身浮雕校徽', '可微波可洗碗机', '精美礼盒包装'],
      specs: '容量：350ml | 材质：优质陶瓷 | 耐高温：120°C'
    },
    {
      id: 3,
      name: '高数期末押题卷',
      description: '高等数学（上下册）期末押题卷，由历年满分学霸团队联合整理，涵盖所有高频考点和必考题型。每套试卷均附详细答案解析和解题思路，命中率高达85%！',
      category: '学习资料',
      points: 50,
      stock: 999,
      sold: 342,
      image: mallImageUrls[2],

      imageBg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      tags: ['限时特惠'],
      features: ['满分学霸团队整理', '命中率高达85%', '详细答案解析', '上下册全覆盖'],
      specs: '格式：PDF高清电子版 | 套数：6套模拟+2套真题 | 附详细解析'
    },
    {
      id: 4,
      name: '校园风景帆布袋',
      description: '环保帆布购物袋，采用16安加厚帆布，承重可达10kg。袋身印有校园标志性风景手绘图案，文艺清新。大容量设计，可装书本、电脑、购物物品，结实耐用。',
      category: '生活用品',
      points: 150,
      stock: 40,
      sold: 67,
      image: mallImageUrls[3],

      imageBg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
      tags: [],
      features: ['16安加厚帆布', '承重10kg', '校园风景手绘', '大容量设计'],
      specs: '尺寸：40×35×10cm | 材质：16安帆布 | 承重：10kg'
    },
    {
      id: 5,
      name: '英语四级词汇手册',
      description: '英语四级核心词汇便携手册，收录3500高频词汇，按考频排序。每个单词附音标、词性、例句、同义词和记忆法。口袋大小，随身携带，利用碎片时间高效背单词。',
      category: '学习资料',
      points: 80,
      stock: 100,
      sold: 215,
      image: mallImageUrls[4],

      imageBg: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      tags: ['热门'],
      features: ['3500高频词汇', '按考频排序', '附例句+记忆法', '口袋便携版'],
      specs: '页数：280页 | 尺寸：口袋版 (10×15cm) | 词汇量：3500词'
    },
    {
      id: 6,
      name: '定制金属U盘 32G',
      description: '校园定制金属U盘，32GB大容量，USB3.0高速传输，读取速度可达100MB/s。全金属外壳，激光雕刻校徽和学号，防水防震。附赠挂绳和转接头，手机电脑两用。',
      category: '数码',
      points: 500,
      stock: 20,
      sold: 45,
      image: mallImageUrls[5],

      imageBg: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
      tags: ['限量'],
      features: ['USB3.0高速传输', '全金属防水防震', '激光雕刻校徽', '手机电脑两用'],
      specs: '容量：32GB | 接口：USB3.0 | 读取：100MB/s | 材质：锌合金'
    },
    {
      id: 7,
      name: '图书馆便携坐垫',
      description: '可折叠便携记忆棉坐垫，图书馆自习必备神器。采用慢回弹记忆棉，久坐不累。防水面料，一擦即净。折叠后仅手掌大小，附带收纳袋和挂扣，随身携带超方便。',
      category: '生活用品',
      points: 120,
      stock: 60,
      sold: 98,
      image: mallImageUrls[6],

      imageBg: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
      tags: [],
      features: ['慢回弹记忆棉', '久坐不累', '防水易清洁', '折叠便携'],
      specs: '展开：35×35×3cm | 折叠：18×18×6cm | 材质：记忆棉+防水布'
    },
    {
      id: 8,
      name: '考研政治思维导图',
      description: '考研政治全套思维导图高清打印版，由985高校政治系学霸团队绘制。涵盖马克思主义基本原理、毛泽东思想、中国近现代史纲要、思想道德修养全部考点，逻辑清晰，一目了然。',
      category: '学习资料',
      points: 60,
      stock: 999,
      sold: 178,
      image: mallImageUrls[7],

      imageBg: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)',
      tags: ['新品'],
      features: ['985学霸团队绘制', '四大模块全覆盖', '逻辑清晰一目了然', '高清可打印'],
      specs: '格式：PDF高清 | 页数：48页 | 覆盖：马原/毛中特/史纲/思修'
    },
    {
      id: 9,
      name: '定制运动水壶',
      description: '校园定制运动水壶，500ml大容量，采用食品级Tritan材质，安全无异味。一键弹盖设计，运动中单手可开。防漏密封，倒置不漏水。壶身印制校园运动标语，活力满满。',
      category: '生活用品',
      points: 180,
      stock: 35,
      sold: 52,
      image: mallImageUrls[8],

      imageBg: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
      tags: [],
      features: ['食品级Tritan材质', '500ml大容量', '一键弹盖单手开', '防漏倒置不漏水'],
      specs: '容量：500ml | 材质：Tritan | 耐温：-10~100°C | 重量：180g'
    },
    {
      id: 10,
      name: '真无线降噪耳机',
      description: '校园定制版真无线蓝牙耳机，主动降噪功能，隔绝环境噪音。续航长达24小时（含充电盒），支持快充10分钟用2小时。蓝牙5.3稳定连接，IPX5防水防汗，运动学习两相宜。',
      category: '数码',
      points: 800,
      stock: 10,
      sold: 23,
      image: mallImageUrls[9],

      imageBg: 'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
      tags: ['限量', '热门'],
      features: ['主动降噪ANC', '续航24小时', '蓝牙5.3稳定', 'IPX5防水防汗'],
      specs: '蓝牙：5.3 | 续航：6h+18h | 降噪：-35dB | 防水：IPX5'
    },
    {
      id: 11,
      name: 'GIS专业实验指导书',
      description: '地理信息系统专业实验指导书，GIS专业学长倾力编写。涵盖ArcGIS、ENVI、QGIS三大主流软件操作教程，包含20个经典实验，每个实验附详细步骤截图和实验数据，零基础也能学会。',
      category: '学习资料',
      points: 90,
      stock: 80,
      sold: 134,
      image: mallImageUrls[10],

      imageBg: 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)',
      tags: ['专业必备'],
      features: ['三大软件全覆盖', '20个经典实验', '附详细步骤截图', '附赠实验数据'],
      specs: '格式：PDF | 页数：156页 | 软件：ArcGIS/ENVI/QGIS | 实验：20个'
    },
    {
      id: 12,
      name: '校园吉祥物抱枕',
      description: '校园定制吉祥物抱枕，采用超柔短毛绒面料，手感细腻亲肤。内填高弹PP棉，蓬松饱满不易变形。40×40cm黄金尺寸，靠坐抱皆宜。枕套可拆洗，经久耐用，是宿舍生活的暖心伴侣。',
      category: '生活用品',
      points: 160,
      stock: 45,
      sold: 71,
      image: mallImageUrls[11],

      imageBg: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
      tags: [],
      features: ['超柔短毛绒面料', '高弹PP棉填充', '枕套可拆洗', '吉祥物定制款'],
      specs: '尺寸：40×40cm | 面料：超柔短毛绒 | 填充：高弹PP棉 | 重量：350g'
    }
  ]
}

export function getMockGoodsDetail(id) {
  const list = getMockGoods()
  return list.find((g) => g.id === Number(id)) || list[0]
}

export function getMockCategories() {
  return ['全部', '学习资料', '生活用品', '文具', '数码']
}

export function getMockRedeemRecords() {
  return [
    { id: 1, goods_id: 3, goods_name: '高数期末押题卷', points: 50, quantity: 1, status: 'delivered', redeem_time: now - 2 * day },
    { id: 2, goods_id: 5, goods_name: '英语四级词汇手册', points: 80, quantity: 1, status: 'shipping', redeem_time: now - 1 * day },
    { id: 3, goods_id: 1, goods_name: '校园定制笔记本', points: 100, quantity: 2, status: 'pending', redeem_time: now - 2 * hour }
  ]
}
