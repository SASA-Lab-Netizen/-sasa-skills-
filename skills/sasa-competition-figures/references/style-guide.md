# 风格规范 & 组件速查（cc-竞赛图表工坊）

## 全局 rcParams（setup() 已封装在 common.py，勿重复设）

```python
font.sans-serif = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
svg.fonttype = 'none'      # 文字保持可编辑节点，不转路径
pdf.fonttype = 42
spines top/right/left/bottom 全关；xtick/ytick size=0；legend.frameon=False
```

## 字号体系

| 元素 | 字号 | 颜色 |
|:---|:---:|:---|
| 居中主标题 | 15 bold | 深红 `#7A2E24` |
| 副标题/口径注 | 9 | `GRAY #8695A3` |
| 左对齐图题 | 15.5 bold | `INK #1B2733` |
| 节点/卡片标题 | 9.5–11 bold | INK |
| 正文/说明 | 7.5–9.6 | `DGRAY #55636F` |
| 小注/英文点缀 | 5.6–7.2 | GRAY |
| 大数字强调 | 11–13 bold | 所在层色 |

## 色板总表

```python
# 暖色家族（层级/传导/漏斗，由浅入深）
W1 #F2B27A   W2 #E88C4A   W3 #C9613A   W4 #96382E
主角橙 ORANGE_MAIN #E8833A
# Nature 多色语义（多系列）
BLUE #4878CF  GREEN #6ACC65  ORANGE #EE854A  PURPLE #B47CC7
CYAN #77BEDB  PINK #D0759F   YELLOW #C4AD66  RED #D65F5F
DGREEN #3A9E5F LBLUE #8ABBE5 NAVY #2E5A88
# 结构色
INK #1B2733  DGRAY #55636F  GRAY #8695A3  LGRAY #C4CFD9  XLGRAY #EDF1F5  PAPER #FFFFFF
```

## 组件速查（全部在 common.py，`from common import *` 即用）

| 组件 | 用途 | 关键参数 |
|:---|:---|:---|
| `canvas(w,h)` | 建画布，equal-aspect，xlim/ylim=(0,w)/(0,h) | figsize 必须 = lim，否则变形 |
| `setup()` | 全局 rcParams | 每个脚本开头调一次 |
| `tint(色, f)` | 任意色调淡作底色 | f=0.86~0.91 |
| `wrap_cjk(t,cols)` | 中文折半换行 | — |
| `title_center(fig,主,副)` | 居中标题（参考图风格） | 深红粗体 |
| `note_bar(ax,x,y,w,h,tag,text)` | 底部左标签+右说明注释条 | tag 深色块 |
| `header(fig,no,title,sub)` | 左对齐图题（论文风） | fig.text 画布层 |
| `rbox / rect / txt / arrow / diamond / dot` | 基础图元 | arrow 支持 rad 弧形、ls 虚线 |
| `state(ax,x,y,w,h,名,副,色)` | 状态机节点 | 浅底+深边圆角 |
| `cond(ax,x,y,s,色)` | 流转条件标签（带白底） | **放目标框正下方**，别塞箭头间隙 |
| `phone(ax,x,y,w,h)` | 手机线框外框 | 配 blk/callout 用 |
| `blk(...)` | 线框占位块 | — |
| `callout(ax,px,py,tx,ty,标签)` | 标注引线（点+线+字） | 线框图标配 |
| `ring(ax,cx,cy,r,nodes,colors,...)` | 环形循环图 | nodes=[(标题,副)]，弧箭头自动避让 |
| `card(...)` | 通用卡片（顶色条+标题+行） | 可带右上角 badge |
| `anno(...)`（各脚本内定义） | 线框图右侧两行标注 | 标题粗+副行灰 |

## 经典构图配方

- **页面布局图** = `phone` + 内部 `blk` 分区 + 右侧 4-6 条 `anno`（标注点在手机右边缘）
- **状态流转图** = 横排 `state` + `arrow` + 条件写目标框下方 + 底部规则 `note_bar`；回退/异常用 `ls='--'` 或 `':'`
- **环形循环图** = `ring()` + 中心 Circle 面板（核心指标大字）+ 底部指标条
- **层级传导图** = 左实色窄块(白字) + 右 tint 宽条(两行) + 层间 arrow + `note_bar`；颜色 W1→W4 逐层加深
- **漏斗图** = 居中 `Polygon` 梯形逐层收口 + 层间转化率标签 + 右侧依据虚线引注
- **雷达图** = 自绘多边形网格（polar 关闭），同心圈 2/4/6/8/10，主角最后画且加 fill alpha 0.16 + marker o
- **阶梯图** = 高度递增 rect 台阶 + 顶部悬浮名称卡 + 台阶间弧形上升箭头

## 输出

```python
save(fig, '图N_名称_子类型', OUT)   # 同时落 .svg 和 300dpi .png
```
