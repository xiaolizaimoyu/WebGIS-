import re

with open('frontend/src/views/ProfileView.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 冲突区域：HEAD是修改密码卡片，dev-C是Tab签到横幅
# 策略：保留HEAD的修改密码卡片，dev-C的Tab部分不要（HEAD已有独立签到卡片）
# 但需要在HEAD的签到横幅里加入"去积分商城"按钮

# 第一步：移除冲突标记，保留HEAD的修改密码卡片，丢弃dev-C的Tab部分
conflict_pattern = re.compile(
    r'<<<<<<< HEAD\n'
    r'(.*?)'  # HEAD内容：修改密码卡片
    r'=======\n'
    r'.*?'   # dev-C内容：Tab签到横幅（丢弃）
    r'>>>>>>> origin/dev-C\n',
    re.DOTALL
)
content = conflict_pattern.sub(r'\1', content)

# 第二步：在HEAD的签到横幅里加入"去积分商城"按钮
# 找到签到按钮，在其后加入商城按钮，并用sign-actions包裹
old_sign_actions = '''          <el-button
            type="primary"
            size="large"
            :class="{ signed: signedToday }"
            :disabled="signedToday"
            :loading="store.signLoading"
            @click="handleSign"
          >
            {{ signedToday ? '✅ 今日已签' : '立即签到 +10' }}
          </el-button>
        </div>'''

new_sign_actions = '''          <div class="sign-actions">
            <el-button
              type="primary"
              size="large"
              :class="{ signed: signedToday }"
              :disabled="signedToday"
              :loading="store.signLoading"
              @click="handleSign"
            >
              {{ signedToday ? '✅ 今日已签' : '立即签到 +10' }}
            </el-button>
            <el-button size="large" @click="router.push('/mall')">
              🎁 去积分商城
            </el-button>
          </div>
        </div>'''

content = content.replace(old_sign_actions, new_sign_actions)

with open('frontend/src/views/ProfileView.vue', 'w', encoding='utf-8') as f:
    f.write(content)

remaining = re.findall(r'^(<<<<<<<|=======|>>>>>>>)', content, re.MULTILINE)
print('残留冲突标记:', remaining if remaining else '无')
print('签到商城按钮已添加:', '去积分商城' in content)
