import re

with open('docs/API.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 冲突1: GET /api/user/me 返回值
pattern1 = re.compile(
    r'<<<<<<< HEAD\n'
    r'成功 data：`\{id, username, nickname, avatar, created_at\}`（avatar 可空）\n'
    r'=======\n'
    r'成功 data：`\{id, username, nickname, avatar, created_at, content_count, comment_count\}`\n'
    r'>>>>>>> origin/dev-D'
)
content = pattern1.sub(
    '成功 data：`{id, username, nickname, avatar, created_at, content_count, comment_count}`（avatar 可空）',
    content
)

# 冲突2: PUT /api/user/password 请求体
pattern2 = re.compile(
    r'<<<<<<< HEAD\n'
    r'请求体：`\{ "old_password": "原密码", "new_password": "至少6位新密码" \}`\n'
    r'=======\n'
    r'请求体：`\{ "old_password": "", "new_password": "至少8位含字母和数字", "confirm_password": "再次输入新密码" \}`\n'
    r'>>>>>>> origin/dev-D'
)
content = pattern2.sub(
    '请求体：`{ "old_password": "", "new_password": "至少8位含字母和数字", "confirm_password": "再次输入新密码" }`',
    content
)

with open('docs/API.md', 'w', encoding='utf-8') as f:
    f.write(content)

remaining = re.findall(r'^(<<<<<<<|=======|>>>>>>>)', content, re.MULTILINE)
print('残留冲突标记:', remaining if remaining else '无')
