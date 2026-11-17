#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_pptx.py — 把结构化内容规格渲染成「可编辑」的 .pptx

设计原则（来自原文档核心主张）：
  - 文字 = 真实文本框（可改），不是图片里的字
  - 表格 = 真实表格（可改），不是截图
  - 色块 = PPT 形状（干净），不是渐变炫技图
  - 每一页按指定版式生成，风格从头到尾统一，无水印、无插画拼贴风

用法：
  python generate_pptx.py spec.json -o output.pptx
  cat spec.json | python generate_pptx.py -o output.pptx

spec.json 结构见本文件底部 EXAMPLE，或 SKILL.md。
"""

import sys
import json
import argparse

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn


# ---------- 颜色 / 字体工具 ----------
def _rgb(hex_str, default="333333"):
    """接受 '0F2C1D' 或 '#0F2C1D'，返回 RGBColor。"""
    if not hex_str:
        hex_str = default
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return RGBColor.from_string(h.upper())


def _set_run(run, text, size, color, bold, font_name):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = font_name
    run.font.color.rgb = color
    # 同时设置东亚字体，确保中文生效
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", font_name)


# ---------- 基础构件 ----------
def _blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def _bg(slide, color):
    # 设置幻灯片背景填充
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = color


def _textbox(slide, left, top, width, height, lines, anchor=MSO_ANCHOR.TOP,
             align=PP_ALIGN.LEFT):
    """
    lines: list of dict {text, size, color, bold, font}
    单一文本框，多段落。
    """
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = ln.get("align", align)
        p.space_after = Pt(ln.get("space_after", 4))
        if ln.get("space_before"):
            p.space_before = Pt(ln["space_before"])
        _set_run(p.add_run(), ln["text"], ln["size"], ln["color"], ln.get("bold", False),
                 ln["font"])
    return tb


def _title_block(slide, style, title, top=0.55, left=0.7, width=11.9, accent=True):
    """统一标题区：标题 + 下方短分割线（强调色）。"""
    _textbox(slide, left, top, width, 0.7,
             [{"text": title, "size": 26, "color": _rgb(style["primary"]),
               "bold": True, "font": style["title_font"], "space_after": 2}])
    if accent:
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top + 0.72),
                                      Inches(1.4), Inches(0.06))
        line.fill.solid()
        line.fill.fore_color.rgb = _rgb(style["accent"])
        line.line.fill.background()
        line.shadow.inherit = False


def _footer(slide, style, meta, idx):
    """页脚：项目名 + 页码。"""
    name = meta.get("title", "")
    tb = slide.shapes.add_textbox(Inches(0.7), Inches(7.05), Inches(9), Inches(0.35))
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    _set_run(p.add_run(), name, 9, _rgb(style["text"]), False, style["body_font"])
    # 页码
    pn = slide.shapes.add_textbox(Inches(12.2), Inches(7.05), Inches(0.9), Inches(0.35))
    tf2 = pn.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    _set_run(p2.add_run(), str(idx), 9, _rgb(style["text"]), False, style["body_font"])


def _image_placeholder(slide, style, left, top, width, height, desc):
    """虚线框 + 居中说明文字，提示此处放什么图。可后续替换。"""
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = _rgb(style["bg"])
    box.line.color.rgb = _rgb(style["accent"])
    box.line.width = Pt(1.25)
    # 虚线
    ln = box.line._get_or_add_ln()
    d = ln.find(qn("a:prstDash"))
    if d is None:
        d = ln.makeelement(qn("a:prstDash"), {})
        ln.append(d)
    d.set("val", "dash")
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _set_run(p.add_run(), "🖼 图片占位\n" + (desc or ""), 12, _rgb(style["accent"]),
             False, style["body_font"])
    return box


# ---------- 各版式渲染 ----------
def _render_cover(slide, style, meta, page):
    _bg(slide, _rgb(style["bg"]))
    # 顶部色带
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0),
                                  Inches(13.333), Inches(0.25))
    band.fill.solid(); band.fill.fore_color.rgb = _rgb(style["accent"]); band.line.fill.background()
    band.shadow.inherit = False
    _textbox(slide, 1.2, 2.4, 10.9, 2.2, [
        {"text": page.get("title", meta.get("title", "")), "size": 44,
         "color": _rgb(style["primary"]), "bold": True, "font": style["title_font"],
         "align": PP_ALIGN.CENTER, "space_after": 10},
        {"text": page.get("subtitle", ""), "size": 20,
         "color": _rgb(style["text"]), "bold": False, "font": style["body_font"],
         "align": PP_ALIGN.CENTER},
    ], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    if page.get("footer") or meta.get("author"):
        _textbox(slide, 1.2, 5.6, 10.9, 0.5, [
            {"text": page.get("footer", meta.get("author", "")), "size": 13,
             "color": _rgb(style["text"]), "bold": False, "font": style["body_font"],
             "align": PP_ALIGN.CENTER},
        ], align=PP_ALIGN.CENTER)


def _render_toc(slide, style, meta, page):
    _bg(slide, _rgb(style["bg"]))
    _title_block(slide, style, page.get("title", "目录"))
    items = page.get("items", [])
    y = 1.7
    for i, it in enumerate(items, 1):
        # 编号圆点
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.9), Inches(y + 0.05),
                                     Inches(0.42), Inches(0.42))
        dot.fill.solid(); dot.fill.fore_color.rgb = _rgb(style["accent"]); dot.line.fill.background()
        dot.shadow.inherit = False
        tf = dot.text_frame; tf.word_wrap = False
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        _set_run(p.add_run(), str(i), 14, _rgb("FFFFFF"), True, style["title_font"])
        _textbox(slide, 1.5, y, 11, 0.5, [
            {"text": it, "size": 16, "color": _rgb(style["text"]), "bold": False,
             "font": style["body_font"]},
        ])
        y += 0.62


def _render_section(slide, style, meta, page):
    _bg(slide, _rgb(style["primary"]))
    _textbox(slide, 1.2, 2.9, 10.9, 2.0, [
        {"text": page.get("title", ""), "size": 40, "color": _rgb("FFFFFF"),
         "bold": True, "font": style["title_font"], "align": PP_ALIGN.CENTER, "space_after": 8},
        {"text": page.get("subtitle", ""), "size": 20, "color": _rgb(style["accent"]),
         "bold": False, "font": style["body_font"], "align": PP_ALIGN.CENTER},
    ], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)


def _render_content(slide, style, meta, page, cols=3):
    """上标题下 N 段（cols=3 为『上标题下三段』，cols=2 可用作简化两列）。"""
    _bg(slide, _rgb(style["bg"]))
    _title_block(slide, style, page.get("title", ""))
    # 结论前置
    if page.get("lead"):
        _textbox(slide, 0.7, 1.5, 11.9, 0.6, [
            {"text": page["lead"], "size": 15, "color": _rgb(style["accent"]), "bold": True,
             "font": style["body_font"]},
        ])
    bullets = page.get("bullets", [])
    top = 2.25
    if cols == 1:
        lines = []
        for b in bullets:
            lines.append({"text": "• " + b, "size": 16, "color": _rgb(style["text"]),
                          "bold": False, "font": style["body_font"], "space_after": 8})
        _textbox(slide, 0.7, top, 11.9, 4.2, lines)
    else:
        col_w = 11.9 / cols
        for i, b in enumerate(bullets[:cols]):
            x = 0.7 + i * col_w
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x + 0.1),
                                          Inches(top), Inches(col_w - 0.2), Inches(3.6))
            card.fill.solid(); card.fill.fore_color.rgb = _rgb("F2F2F2")
            card.line.color.rgb = _rgb(style["primary"]); card.line.width = Pt(0.75)
            card.shadow.inherit = False
            tf = card.text_frame; tf.word_wrap = True
            tf.margin_left = Inches(0.18); tf.margin_right = Inches(0.18)
            tf.margin_top = Inches(0.2)
            p = tf.paragraphs[0]
            _set_run(p.add_run(), b, 15, _rgb(style["text"]), False, style["body_font"])


def _render_grid2x2(slide, style, meta, page):
    """田字格 2x2 均分。"""
    _bg(slide, _rgb(style["bg"]))
    _title_block(slide, style, page.get("title", ""))
    cells = page.get("cells", [])
    gx, gy = 0.7, 1.7
    cw, ch = 5.85, 2.35
    gap = 0.2
    for i, c in enumerate(cells[:4]):
        r, col = divmod(i, 2)
        x = gx + col * (cw + gap)
        y = gy + r * (ch + gap)
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y),
                                      Inches(cw), Inches(ch))
        card.fill.solid(); card.fill.fore_color.rgb = _rgb("FFFFFF")
        card.line.color.rgb = _rgb(style["primary"]); card.line.width = Pt(1)
        card.shadow.inherit = False
        tf = card.text_frame; tf.word_wrap = True
        tf.margin_left = Inches(0.22); tf.margin_right = Inches(0.22); tf.margin_top = Inches(0.22)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), c.get("title", ""), 16, _rgb(style["accent"]), True,
                 style["title_font"])
        if c.get("text"):
            p2 = tf.add_paragraph(); p2.space_before = Pt(6)
            _set_run(p2.add_run(), c["text"], 13, _rgb(style["text"]), False, style["body_font"])


def _render_image_text(slide, style, meta, page):
    """左图右文 / 左文右图（side='left' 表示图在左）。"""
    _bg(slide, _rgb(style["bg"]))
    _title_block(slide, style, page.get("title", ""))
    side = page.get("side", "left")
    if side == "left":
        img_left, txt_left = 0.7, 6.6
    else:
        img_left, txt_left = 6.6, 0.7
    # 图片占位
    _image_placeholder(slide, style, img_left, 1.7, 5.9, 4.6, page.get("image_desc", ""))
    # 文本块
    blocks = page.get("blocks", [])
    y = 1.8
    for b in blocks:
        val = b.get("value")
        lines = []
        if val:
            lines.append({"text": val, "size": 30, "color": _rgb(style["accent"]),
                          "bold": True, "font": style["title_font"], "space_after": 2})
        lines.append({"text": b.get("label", ""), "size": 14, "color": _rgb(style["text"]),
                      "bold": False, "font": style["body_font"]})
        _textbox(slide, txt_left, y, 5.9, 1.3, lines)
        y += 1.5


def _render_three_cards(slide, style, meta, page):
    """三等分卡片。"""
    _bg(slide, _rgb(style["bg"]))
    _title_block(slide, style, page.get("title", ""))
    cards = page.get("cards", [])
    gx, gy, cw, ch = 0.7, 1.8, 3.85, 4.4
    gap = 0.18
    for i, c in enumerate(cards[:3]):
        x = gx + i * (cw + gap)
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(gy),
                                      Inches(cw), Inches(ch))
        card.fill.solid(); card.fill.fore_color.rgb = _rgb("FFFFFF")
        card.line.color.rgb = _rgb(style["accent"]); card.line.width = Pt(1)
        card.shadow.inherit = False
        tf = card.text_frame; tf.word_wrap = True
        tf.margin_left = Inches(0.25); tf.margin_right = Inches(0.25); tf.margin_top = Inches(0.3)
        p = tf.paragraphs[0]
        _set_run(p.add_run(), c.get("title", ""), 17, _rgb(style["primary"]), True,
                 style["title_font"])
        if c.get("text"):
            p2 = tf.add_paragraph(); p2.space_before = Pt(8)
            _set_run(p2.add_run(), c["text"], 13, _rgb(style["text"]), False, style["body_font"])


def _render_table(slide, style, meta, page):
    """上标题下表格（真实可编辑表格）。"""
    _bg(slide, _rgb(style["bg"]))
    _title_block(slide, style, page.get("title", ""))
    header = page.get("header", [])
    rows = page.get("rows", [])
    n_rows = len(rows) + 1
    n_cols = max(len(header), *(len(r) for r in rows)) if rows else len(header)
    n_cols = max(n_cols, 1)
    tbl_shape = slide.shapes.add_table(n_rows, n_cols, Inches(0.7), Inches(1.7),
                                       Inches(11.9), Inches(0.4 * n_rows))
    table = tbl_shape.table
    # 列宽均分
    col_w = 11.9 / n_cols
    for ci in range(n_cols):
        table.columns[ci].width = Inches(col_w)
    # 表头
    for ci, h in enumerate(header[:n_cols]):
        cell = table.cell(0, ci)
        cell.fill.solid(); cell.fill.fore_color.rgb = _rgb(style["primary"])
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        _set_run(p.add_run(), str(h), 13, _rgb("FFFFFF"), True, style["title_font"])
    # 数据行
    for ri, row in enumerate(rows, 1):
        for ci in range(n_cols):
            cell = table.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _rgb("F7F7F7") if ri % 2 else _rgb("FFFFFF")
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            val = row[ci] if ci < len(row) else ""
            _set_run(p.add_run(), str(val), 12, _rgb(style["text"]), False, style["body_font"])


RENDERERS = {
    "cover": _render_cover,
    "toc": _render_toc,
    "section": _render_section,
    "content": lambda s, st, m, p: _render_content(s, st, m, p, cols=p.get("cols", 3)),
    "grid2x2": _render_grid2x2,
    "image_text": _render_image_text,
    "three_cards": _render_three_cards,
    "table": _render_table,
}


def build(spec, out_path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    style = spec.get("style", {})
    style.setdefault("primary", "0F2C1D")
    style.setdefault("accent", "FF6B00")
    style.setdefault("bg", "FFFFFF")
    style.setdefault("text", "333333")
    style.setdefault("title_font", "Microsoft YaHei")
    style.setdefault("body_font", "Microsoft YaHei")
    meta = spec.get("meta", {})

    for idx, page in enumerate(spec.get("pages", []), 1):
        ptype = page.get("type", "content")
        renderer = RENDERERS.get(ptype, _render_content)
        slide = _blank_slide(prs)
        renderer(slide, style, meta, page)
        # 封面/过渡页不加页脚页码
        if ptype not in ("cover", "section"):
            _footer(slide, style, meta, idx)

    prs.save(out_path)
    return out_path


EXAMPLE = {
    "meta": {"title": "XX 品牌校园营销策划案", "author": "飒飒"},
    "style": {
        "primary": "0F2C1D", "accent": "FF6B00", "bg": "FFFFFF", "text": "333333",
        "title_font": "Microsoft YaHei", "body_font": "Microsoft YaHei"
    },
    "pages": [
        {"type": "cover", "title": "XX 品牌校园营销策划案",
         "subtitle": "2026 春季校园行 · 商赛参赛作品", "footer": "参赛团队：一个人也能赢"},
        {"type": "toc", "title": "目录",
         "items": ["项目背景与市场洞察", "产品卖点与差异化", "营销策略与节奏", "预算与预期回报"]},
        {"type": "section", "title": "01", "subtitle": "项目背景与市场洞察"},
        {"type": "content", "title": "市场洞察：Z 世代喝饮料的三大动机",
         "lead": "结论：情绪价值 > 功能价值，校园场景是突破口。",
         "bullets": ["社交货币：好看好拍才能自发传播", "性价比敏感：单价敏感但愿为颜值买单",
                     "健康焦虑：低糖零卡是入场券"]},
        {"type": "grid2x2", "title": "竞品四象限",
         "cells": [{"title": "传统大牌", "text": "渠道强、年轻感弱"},
                   {"title": "网红新锐", "text": "声量高、复购不稳"},
                   {"title": "白牌低价", "text": "便宜但无记忆点"},
                   {"title": "我们的机会", "text": "高颜值 + 真零卡 + 校园梗"}]},
        {"type": "image_text", "title": "主推产品：气泡电解质水", "side": "left",
         "image_desc": "一瓶饮料站立在纯白背景中，带冷凝水珠与高光",
         "blocks": [{"value": "0糖", "label": "真零卡，无负担"},
                    {"value": "5种", "label": "校园限定口味"},
                    {"value": "¥6", "label": "学生友好定价"}]},
        {"type": "three_cards", "title": "三大营销策略",
         "cards": [{"title": "快闪打卡", "text": "食堂门口设冷凝水珠装置，引发拍照"},
                   {"title": "宿舍种草", "text": "招募校园 KOC 做开箱"},
                   {"title": "考试季陪伴", "text": "期末复习包联名"}]},
        {"type": "table", "title": "预算分配（单位：元）",
         "header": ["项目", "金额", "占比"],
         "rows": [["快闪物料", "8000", "40%"], ["KOC 投放", "6000", "30%"],
                  ["联名包装", "4000", "20%"], ["备用", "2000", "10%"]]},
    ]
}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="把结构化规格渲染成可编辑 .pptx")
    ap.add_argument("spec", nargs="?", help="spec.json 路径；省略则从 stdin 读取")
    ap.add_argument("-o", "--output", default="output.pptx", help="输出 .pptx 路径")
    ap.add_argument("--example", action="store_true", help="打印示例 spec.json 后退出")
    args = ap.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, ensure_ascii=False, indent=2))
        return

    if args.spec:
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    else:
        spec = json.load(sys.stdin)

    out = build(spec, args.output)
    print(f"✅ 已生成可编辑 PPTX：{out}（共 {len(spec.get('pages', []))} 页）")


if __name__ == "__main__":
    main()
