"""SVG 图形验证码生成（归属：后端 D）

纯标准库实现（random/base64），不引入 Pillow 等第三方依赖：
- 字符集去掉了易混淆的 0/O/1/I，降低用户输入错误率
- 输出为 SVG 源码 -> base64 data URL，前端 <img :src> 直接绑定即可
- 随机字体大小 / 旋转 / 颜色 + 干扰线 + 干扰点，肉眼可读、机器难识别

安全提示：本项目验证码仅用于登录防机器人，采用"后端存储答案、
前端只拿图片"的模式，答案绝不随图片下发。
"""
import base64
import secrets

# 字符集：去掉易混淆的 0/O、1/I/L
CAPTCHA_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
# 验证码位数
CODE_LENGTH = 4

# SVG 画布尺寸
_SVG_W, _SVG_H = 120, 40
# 字符/干扰元素用的高对比配色
_PALETTE = ["#e03131", "#1971c2", "#2f9e44", "#f08c00", "#6741d9", "#0c8599"]


def generate_captcha_text(length: int = CODE_LENGTH) -> str:
    """生成随机验证码文本（加密安全随机源）。"""
    return "".join(secrets.choice(CAPTCHA_CHARS) for _ in range(length))


def render_captcha_svg(text: str) -> str:
    """把验证码文本渲染成 SVG 源码（纯标准库）。"""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SVG_W}" height="{_SVG_H}" '
        f'viewBox="0 0 {_SVG_W} {_SVG_H}">',
        # 浅色背景
        '<rect width="100%" height="100%" fill="#f5f7fa"/>',
    ]
    # 干扰线：4 条随机斜线
    for _ in range(4):
        x1, y1 = secrets.randbelow(_SVG_W), secrets.randbelow(_SVG_H)
        x2, y2 = secrets.randbelow(_SVG_W), secrets.randbelow(_SVG_H)
        color = _PALETTE[secrets.randbelow(len(_PALETTE))]
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="1" opacity="0.5"/>'
        )
    # 字符：逐个绘制，随机大小/旋转/颜色/纵向偏移
    slot = _SVG_W / (len(text) + 1)
    for i, ch in enumerate(text):
        x = slot * (i + 0.5) + secrets.randbelow(9) - 4
        y = _SVG_H / 2 + 8 + secrets.randbelow(9) - 4
        size = 22 + secrets.randbelow(7)
        rot = secrets.randbelow(51) - 25
        color = _PALETTE[secrets.randbelow(len(_PALETTE))]
        parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" '
            f'font-family="Georgia, Arial, sans-serif" font-weight="bold" '
            f'text-anchor="middle" transform="rotate({rot} {x:.1f} {y:.1f})">{ch}</text>'
        )
    # 干扰点：30 个随机圆点
    for _ in range(30):
        cx, cy = secrets.randbelow(_SVG_W), secrets.randbelow(_SVG_H)
        color = _PALETTE[secrets.randbelow(len(_PALETTE))]
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="1" fill="{color}" opacity="0.6"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def svg_to_data_url(svg: str) -> str:
    """SVG 源码转 base64 data URL，前端 <img :src> 直接可用。"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def generate_captcha(length: int = CODE_LENGTH) -> tuple[str, str]:
    """一步到位：返回 (验证码文本, 图片 data URL)。

    文本由调用方自行保存校验，图片直接下发给前端展示。
    """
    text = generate_captcha_text(length)
    return text, svg_to_data_url(render_captcha_svg(text))
