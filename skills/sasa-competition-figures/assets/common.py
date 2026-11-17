# -*- coding: utf-8 -*-
"""后来的答案 · 图表公共样式库 v6.1（黑体大字版）

v6 相对 v5 的升级：
1. 配色降饱和：暖赭主色 + 低饱和语义色 + 暖灰阶，去"塑料感"
2. 质感细节：细描边、小圆角、左侧色条、微妙投影、英文 kicker 点缀
3. 纸白底 #FDFCFA，告别纯白的廉价感
v6.1（2026-09-08 用户要求）：
4. 文字全部改为纯黑/近黑，不用灰色
5. 字号整体放大一档（标题 16.5 / 正文 10 / 小注 8.5）
API 与 v5 兼容，旧脚本可直接重跑获得新风格。
"""
import os, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle, Wedge
from matplotlib.colors import to_rgb

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- 主色（暖赭橙，视觉主角） ----------------
BRAND   = '#B8551F'
BRAND_L = '#E3A072'
BRAND_D = '#7E3512'

# ---------------- 暖色家族（层级 / 传导 / 漏斗，由浅入深） ----------------
W1 = '#E8C39C'
W2 = '#DD9A5E'
W3 = '#C0642F'
W4 = '#8C3F1E'

# ---------------- 语义色（低饱和，多系列对比用） ----------------
BLUE   = '#3F6E91'
GREEN  = '#6E904F'
ORANGE = '#C9912F'
PURPLE = '#8A5C8D'
CYAN   = '#50899E'
PINK   = '#B4697C'
YELLOW = '#AC8B2E'
RED    = '#9E453D'
DGREEN = '#4F7A50'
LBLUE  = '#7C9DB8'
NAVY   = '#2B4962'

# ---------------- 文字色：纯黑体系（用户要求，不用灰） ----------------
INK    = '#000000'   # 标题
BODY   = '#000000'   # 正文
SUB    = '#1A1A1A'   # 小注（近黑）

# ---------------- 线条 / 填充（非文字，可浅） ----------------
HAIR   = '#B9B0A5'   # 细线
FILL   = '#EFEAE3'   # 浅填充
PAPER  = '#FDFCFA'
SHADOW = '#DED7CD'
LINE   = '#5A5A5A'   # 箭头 / 引线（深灰，非文字）

# 兼容旧名
DGRAY  = BODY
GRAY   = SUB
LGRAY  = HAIR
XLGRAY = FILL

SEQ6 = [BLUE, GREEN, ORANGE, PURPLE, CYAN, PINK]
SEQ4 = [BLUE, GREEN, ORANGE, PURPLE]
TINTS = ['#E4EDF4', '#E6EFE2', '#F7EEDA', '#EFE6F0', '#E1EEF4', '#F6E7EB']

FS = dict(
    title=16.5, sub=10.0, card=10.6, body=10.0, note=8.6,
    kicker=7.6, metric=17.5, mini=9.0,
)


def setup():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
        'axes.unicode_minus': False,
        'svg.fonttype': 'none',
        'pdf.fonttype': 42,
        'axes.spines.right': False, 'axes.spines.top': False,
        'axes.spines.left': False,  'axes.spines.bottom': False,
        'xtick.major.size': 0, 'ytick.major.size': 0,
        'legend.frameon': False,
    })


def tint(hexc, f=0.80):
    r, g, b = to_rgb(hexc)
    return (r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f)


def wrap_cjk(t, cols=6):
    if len(t) <= cols:
        return t
    h = (len(t) + 1) // 2
    return t[:h] + '\n' + t[h:]


def canvas(w=11.0, h=7.4, bg=PAPER):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')
    return fig, ax


def header(fig, no, title, sub, x=0.046, top=0.964, gap=0.046):
    fig.text(x, top, '%s　%s' % (no, title), fontsize=FS['title'],
             weight='bold', color=INK, va='top', ha='left')
    fig.text(x, top - gap, sub, fontsize=FS['sub'], color=SUB, va='top', ha='left')


def title_center(fig, text, sub=None, y=0.948, gap=0.052):
    fig.text(0.5, y, text, fontsize=FS['title'], weight='bold', color=BRAND_D,
             ha='center', va='top')
    if sub:
        fig.text(0.5, y - gap, sub, fontsize=FS['sub'], color=SUB,
                 ha='center', va='top')


def save(fig, name, outdir=None):
    outdir = outdir or HERE
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(os.path.join(outdir, name + '.svg'), bbox_inches='tight',
                dpi=300, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(outdir, name + '.png'), bbox_inches='tight',
                dpi=300, facecolor=fig.get_facecolor())
    plt.close(fig)
    print('  ok  ' + name)


# ---------------- 基础图元 ----------------
def shadow(ax, x, y, w, h, r=0.07, z=2, off=0.035, color=SHADOW):
    ax.add_patch(FancyBboxPatch((x + off, y - off), w, h,
                 boxstyle="round,pad=0,rounding_size=%s" % r,
                 linewidth=0, facecolor=color, zorder=z, mutation_aspect=1.0))


def rbox(ax, x, y, w, h, fc=PAPER, ec=HAIR, lw=0.9, r=0.07, z=3,
         alpha=1.0, ls='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0,rounding_size=%s" % r,
                 linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z,
                 alpha=alpha, linestyle=ls, mutation_aspect=1.0))


def rect(ax, x, y, w, h, fc=FILL, ec='none', lw=0, z=3, alpha=1.0):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                           linewidth=lw, zorder=z, alpha=alpha))


def txt(ax, x, y, s, size=None, color=BODY, weight='normal', ha='center',
        va='center', z=5, ls=1.35):
    ax.text(x, y, s, fontsize=size or FS['body'], color=color, weight=weight,
            ha=ha, va=va, zorder=z, linespacing=ls)


def kicker(ax, x, y, s, size=None, color=SUB, ha='left', z=5):
    ax.text(x, y, s, fontsize=size or FS['kicker'], color=color, ha=ha,
            va='center', zorder=z)


def metric(ax, x, y, s, size=None, color=BRAND, ha='center', z=5, unit=None):
    size = size or FS['metric']
    ax.text(x, y, s, fontsize=size, color=color, weight='bold', ha=ha,
            va='center', zorder=z)
    if unit:
        ax.text(x + len(s) * size * 0.0092 + 0.08, y - size * 0.004, unit,
                fontsize=size * 0.42, color=SUB, ha='left', va='center',
                zorder=z)


def arrow(ax, x1, y1, x2, y2, color=LINE, lw=1.5, style='-|>', ls='-',
          rad=0.0, z=2, sa=0, sb=0):
    cs = 'arc3,rad=%s' % rad if rad else 'arc3'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), zorder=z,
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                linestyle=ls, shrinkA=sa, shrinkB=sb,
                                connectionstyle=cs))


def diamond(ax, cx, cy, d, fc=PAPER, ec=LINE, lw=1.1, z=4):
    ax.add_patch(Polygon([(cx, cy + d / 2), (cx + d / 2, cy),
                          (cx, cy - d / 2), (cx - d / 2, cy)],
                         closed=True, facecolor=fc, edgecolor=ec,
                         linewidth=lw, zorder=z))


def dot(ax, x, y, r=0.032, fc=LINE, z=6):
    ax.add_patch(Circle((x, y), r, facecolor=fc, edgecolor='none', zorder=z))


# ---------------- 复合组件 ----------------
def panel(ax, x, y, w, h, title=None, color=BRAND, z=3, kicker_text=None):
    rbox(ax, x, y, w, h, fc=tint(color, 0.93), ec=tint(color, 0.70),
         lw=0.9, r=0.08, z=z)
    if title:
        txt(ax, x + 0.22, y + h - 0.30, title, size=FS['card'], weight='bold',
            color=INK, ha='left', z=z + 2)
    if kicker_text:
        kicker(ax, x + w - 0.22, y + h - 0.28, kicker_text, ha='right', z=z + 2)


def state(ax, x, y, w, h, name, sub=None, color=BLUE, z=4, fs=None, sfs=None,
          en=None):
    """状态机节点：白底 + 左侧色条 + 细边"""
    shadow(ax, x, y, w, h, r=0.075, z=z - 1)
    rbox(ax, x, y, w, h, fc=PAPER, ec=HAIR, lw=0.9, r=0.075, z=z)
    rect(ax, x + 0.015, y + 0.015, 0.062, h - 0.03, fc=color, z=z + 1)
    tx = x + 0.20
    if sub:
        txt(ax, tx, y + h * 0.66, name, size=fs or FS['card'], weight='bold',
            color=INK, ha='left', z=z + 2)
        txt(ax, tx, y + h * 0.31, sub, size=sfs or FS['note'], color=SUB,
            ha='left', z=z + 2)
    else:
        txt(ax, tx, y + h / 2, name, size=fs or FS['card'], weight='bold',
            color=INK, ha='left', z=z + 2)
    if en:
        kicker(ax, x + w - 0.16, y + h - 0.24, en, ha='right', z=z + 2)


def cond(ax, x, y, s, color=SUB, fs=None, z=6):
    """流转条件胶囊"""
    fs = fs or FS['note']
    w = max(1.55, len(s) * 0.185 + 0.36)
    rbox(ax, x - w / 2, y - 0.155, w, 0.31, fc=PAPER, ec=tint(color, 0.45),
         lw=0.85, r=0.155, z=z)
    txt(ax, x, y, s, size=fs, color=color, z=z + 1)


def phone(ax, x, y, w, h, r=0.15):
    shadow(ax, x, y, w, h, r=r, z=2, off=0.05)
    rbox(ax, x, y, w, h, fc=PAPER, ec='#9E958A', lw=1.2, r=r, z=3)
    rect(ax, x + w * 0.38, y + h - 0.22, w * 0.24, 0.08, fc='#BDB4A8', z=4)


def blk(ax, x, y, w, h, label='', fc=PAPER, ec=HAIR, lw=0.9, fs=None,
        color=BODY, z=5, weight='normal', r=0.05, align='center',
        bar=None, kicker_text=None):
    rbox(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, r=r, z=z)
    if bar:
        rect(ax, x + 0.012, y + 0.012, 0.05, h - 0.024, fc=bar, z=z + 1)
    if kicker_text:
        kicker(ax, x + w - 0.11, y + h - 0.17, kicker_text, ha='right', z=z + 1)
    if label:
        tx = x + w / 2 if align == 'center' else x + 0.16
        ha = 'center' if align == 'center' else 'left'
        txt(ax, tx, y + h / 2, label, size=fs or FS['mini'], color=color,
            weight=weight, z=z + 1, ha=ha)


def callout(ax, px, py, tx, ty, label, color=LINE, fs=None, lw=0.9,
            side='right', z=6, sub=None):
    ax.annotate('', xy=(px, py), xytext=(tx, ty), zorder=z,
                arrowprops=dict(arrowstyle='-', color=color, lw=lw,
                                shrinkA=0, shrinkB=0, connectionstyle='arc3'))
    dot(ax, px, py, 0.030, color, z=z + 1)
    ha = 'left' if side == 'right' else 'right'
    ox = 0.14 if side == 'right' else -0.14
    txt(ax, tx + ox, ty + (0.15 if sub else 0), label, size=fs or FS['mini'],
        weight='bold', color=INK, ha=ha, z=z + 1)
    if sub:
        txt(ax, tx + ox, ty - 0.20, sub, size=FS['note'], color=SUB, ha=ha,
            z=z + 1)


def ring(ax, cx, cy, r, nodes, colors, bw=2.05, bh=0.90, start=90,
         fs=None, sfs=None, arc_lw=1.6, gap_deg=17):
    fs = fs or FS['mini']
    sfs = sfs or FS['note']
    n = len(nodes)
    pts = []
    for i in range(n):
        a = math.radians(start - 360.0 * i / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a1 = math.atan2(y1 - cy, x1 - cx)
        a2 = math.atan2(y2 - cy, x2 - cx)
        d = math.degrees(a2 - a1)
        d = (d + 360) % 360
        if d > 180:
            d -= 360
        sg = math.copysign(1, d)
        g1 = math.radians(math.degrees(a1) - gap_deg / 2.0 * sg)
        g2 = math.radians(math.degrees(a2) + gap_deg / 2.0 * sg)
        arrow(ax, cx + r * math.cos(g1), cy + r * math.sin(g1),
              cx + r * math.cos(g2), cy + r * math.sin(g2),
              color=colors[i], lw=arc_lw, rad=0.15 * sg, z=3)
    for i, ((t, s), (x, y)) in enumerate(zip(nodes, pts)):
        c = colors[i]
        shadow(ax, x - bw / 2, y - bh / 2, bw, bh, r=0.075, z=4, off=0.03)
        rbox(ax, x - bw / 2, y - bh / 2, bw, bh, fc=PAPER, ec=HAIR, lw=0.9,
             r=0.075, z=5)
        rect(ax, x - bw / 2 + 0.012, y - bh / 2 + 0.012, 0.05, bh - 0.024,
             fc=c, z=6)
        txt(ax, x + 0.03, y + (bh * 0.15 if s else 0), t, size=fs,
            weight='bold', color=INK, z=7)
        if s:
            txt(ax, x + 0.03, y - bh * 0.23, s, size=sfs, color=SUB, z=7)
    return pts


def card(ax, x, y, w, h, title, lines, color=BRAND, fs=None, lfs=None, z=4,
         badge=None, bfs=None, no=None, big=None, big_unit=None):
    fs = fs or FS['card']
    lfs = lfs or FS['note']
    shadow(ax, x, y, w, h, r=0.08, z=z - 1, off=0.04)
    rbox(ax, x, y, w, h, fc=PAPER, ec=HAIR, lw=0.9, r=0.08, z=z)
    rect(ax, x + 0.02, y + h - 0.08, w - 0.04, 0.08, fc=color, z=z + 1)
    txt(ax, x + w / 2, y + h - 0.36, title, size=fs, weight='bold',
        color=INK, z=z + 2)
    if no is not None:
        ax.add_patch(Circle((x + w - 0.34, y + h - 0.38), 0.175,
                            facecolor=tint(color, 0.86), edgecolor='none',
                            zorder=z + 2))
        txt(ax, x + w - 0.34, y + h - 0.38, str(no), size=FS['mini'],
            weight='bold', color=BRAND_D, z=z + 3)
    if big:
        metric(ax, x + w / 2, y + h - 1.06, big, size=FS['metric'],
               color=color, z=z + 2, unit=big_unit)
    if lines:
        n = len(lines)
        top0 = y + h - (1.52 if big else 0.66)
        step = (top0 - y - 0.20) / n
        for i, ln in enumerate(lines):
            txt(ax, x + w / 2, top0 - step * (i + 0.5), ln, size=lfs,
                color=BODY, z=z + 2)
    if badge:
        bfs = bfs or FS['note']
        bw = len(badge) * bfs * 0.15 + 0.28
        rbox(ax, x + w - bw - 0.16, y + h + 0.06, bw, 0.30, fc=color,
             ec='none', lw=0, r=0.06, z=z + 3)
        txt(ax, x + w - bw / 2 - 0.16, y + h + 0.21, badge, size=bfs,
            weight='bold', color=PAPER, z=z + 4)


def note_bar(ax, x, y, w, h, tag, text, tagc=BRAND_D, z=3):
    rbox(ax, x, y, w, h, fc=tint(tagc, 0.93), ec=tint(tagc, 0.72), lw=0.9,
         r=0.06, z=z)
    tw = len(tag) * 0.235 + 0.40
    rbox(ax, x + 0.15, y + (h - 0.46) / 2, tw, 0.46, fc=tagc, ec='none',
         lw=0, r=0.05, z=z + 1)
    txt(ax, x + 0.15 + tw / 2, y + h / 2, tag, size=FS['mini'], weight='bold',
        color=PAPER, z=z + 2)
    txt(ax, x + 0.15 + tw + 0.30, y + h / 2, text, size=FS['mini'], color=SUB,
        ha='left', z=z + 2)
