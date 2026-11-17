# -*- coding: utf-8 -*-
"""
PRD Document Generator
Reads a JSON spec and generates a formatted .docx PRD document.
Usage:
    python generate_prd.py input.json output.docx
    python generate_prd.py  # interactive mode, reads from stdin
"""
import sys
import json
import os

sys.stdout.reconfigure(encoding='utf-8')

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("ERROR: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)


def set_cell_background(cell, color_hex):
    """Set cell background color."""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color_hex)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_text(cell, text, bold=False, size=10, color=None, alignment=None):
    """Set cell text with formatting."""
    cell.text = ""
    p = cell.paragraphs[0]
    if alignment:
        p.alignment = alignment
    run = p.add_run(str(text))
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_table_from_data(doc, headers, rows, header_color="4472C4"):
    """Add a formatted table to the document."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_text(cell, header, bold=True, size=10, color=(255, 255, 255),
                      alignment=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_background(cell, header_color)

    # Data rows
    for row_idx, row_data in enumerate(rows):
        for col_idx, cell_data in enumerate(row_data):
            cell = table.rows[row_idx + 1].cells[col_idx]
            # Handle multi-line cell content
            text = str(cell_data).replace('\\n', '\n')
            if '\n' in text:
                cell.text = ""
                for line_idx, line in enumerate(text.split('\n')):
                    if line_idx > 0:
                        cell.add_paragraph()
                    p = cell.paragraphs[-1]
                    run = p.add_run(line)
                    run.font.size = Pt(10)
            else:
                set_cell_text(cell, text, size=10)

    return table


def add_heading(doc, text, level=1):
    """Add a heading with custom formatting."""
    heading = doc.add_heading(text, level=level)
    return heading


def add_code_block(doc, text):
    """Add a code block (monospace, bordered)."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    # Set East Asian font
    run.font.element.rPr.rFonts.set(qn('w:eastAsia'), 'Courier New')
    p.paragraph_format.left_indent = Cm(0.5)
    return p


def generate_prd(prd_data, output_path):
    """Generate a PRD docx from structured data."""
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Microsoft YaHei'
    font.size = Pt(10.5)
    font.element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')

    # Title
    title = doc.add_heading(prd_data.get('title', '产品需求文档（PRD）'), level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle.add_run(prd_data.get('subtitle', ''))
    sub_run.font.size = Pt(14)
    sub_run.font.color.rgb = RGBColor(89, 89, 89)

    doc.add_paragraph()  # spacing

    # Process sections
    for section in prd_data.get('sections', []):
        section_type = section.get('type', 'paragraph')

        if section_type == 'heading':
            add_heading(doc, section['text'], level=section.get('level', 1))

        elif section_type == 'paragraph':
            p = doc.add_paragraph(section.get('text', ''))
            if section.get('bold'):
                for run in p.runs:
                    run.bold = True

        elif section_type == 'bullet':
            for item in section.get('items', []):
                doc.add_paragraph(item, style='List Bullet')

        elif section_type == 'code':
            add_code_block(doc, section.get('text', ''))

        elif section_type == 'table':
            headers = section.get('headers', [])
            rows = section.get('rows', [])
            add_table_from_data(doc, headers, rows)
            doc.add_paragraph()  # spacing after table

        elif section_type == 'spacer':
            doc.add_paragraph()

    # Save
    doc.save(output_path)
    return output_path


def interactive_mode():
    """Read PRD JSON from stdin and generate docx."""
    print("=== sasa-prd-generator ===")
    print("Paste PRD JSON spec (Ctrl+D or empty line to finish):")

    lines = []
    try:
        while True:
            line = input()
            if line == '':
                break
            lines.append(line)
    except EOFError:
        pass

    json_str = '\n'.join(lines)
    try:
        prd_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return

    output = input("Output path (default: prd_output.docx): ").strip()
    if not output:
        output = "prd_output.docx"

    generate_prd(prd_data, output)
    print(f"Generated: {output}")


def main():
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        with open(input_path, 'r', encoding='utf-8') as f:
            prd_data = json.load(f)
        generate_prd(prd_data, output_path)
        print(f"Generated: {output_path}")
    elif len(sys.argv) == 2:
        # Single argument = JSON file path, output to same dir
        input_path = sys.argv[1]
        with open(input_path, 'r', encoding='utf-8') as f:
            prd_data = json.load(f)
        output_path = os.path.splitext(input_path)[0] + '.docx'
        generate_prd(prd_data, output_path)
        print(f"Generated: {output_path}")
    else:
        interactive_mode()


if __name__ == '__main__':
    main()

