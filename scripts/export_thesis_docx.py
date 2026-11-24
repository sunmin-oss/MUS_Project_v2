from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from pathlib import Path
import re

root = Path(r"D:\大學\專題\MUS_Project_v2")
input_path = root / "論文" / "論文範本.md"
output_path = root / "論文" / "論文範本_Word版.docx"

text = input_path.read_text(encoding='utf-8')

# Remove HTML comments and div wrappers to keep content readable
text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
text = text.replace('<div align="center">', '').replace('</div>', '')

# Normalize newlines
text = text.replace('\r\n', '\n').replace('\r', '\n')

# Split into lines
lines = text.split('\n')

# Create document
doc = Document()

# Default style
style = doc.styles['Normal']
style.font.name = '標楷體'
style.font.size = Pt(10.5)
style.paragraph_format.line_spacing = 1.15
style.paragraph_format.space_after = Pt(4)

# Set East Asian font explicitly for compatibility
style._element.rPr.rFonts.set(qn('w:eastAsia'), '標楷體')

# Section setup: A4, margins
section = doc.sections[0]
section.top_margin = Cm(2.8)
section.bottom_margin = Cm(2.5)
section.left_margin = Cm(3.0)
section.right_margin = Cm(3.0)

# Add title block
paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = paragraph.add_run('基於 RAG 技術之智慧藥物辨識與用藥管理系統')
run.font.name = '標楷體'
run.font.size = Pt(16)
run.bold = True

paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = paragraph.add_run('國立高雄科技大學電子工程系')
run.font.name = '標楷體'
run.font.size = Pt(12)

paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = paragraph.add_run('指導老師：XXX')
run.font.name = '標楷體'
run.font.size = Pt(12)

paragraph = doc.add_paragraph()
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = paragraph.add_run('作者：XXX　XXX　XXX')
run.font.name = '標楷體'
run.font.size = Pt(12)

# Add abstract heading
paragraph = doc.add_paragraph()
paragraph.add_run('摘要').bold = True

# Parse content sections based on markdown headings
# We will keep the content as plain paragraphs and headings.
for line in lines:
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith('# '):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(stripped[2:])
        r.font.name = '標楷體'
        r.font.size = Pt(14)
        r.bold = True
    elif stripped.startswith('## '):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        r = p.add_run(stripped[3:])
        r.font.name = '標楷體'
        r.font.size = Pt(12)
        r.bold = True
    elif stripped.startswith('### '):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        r = p.add_run(stripped[4:])
        r.font.name = '標楷體'
        r.font.size = Pt(11)
        r.bold = True
    elif stripped.startswith('|'):
        # Keep tables as plain text lines
        p = doc.add_paragraph()
        p.add_run(stripped)
    elif stripped.startswith('!['):
        # Skip image markdown lines
        continue
    elif stripped.startswith('**圖') or stripped.startswith('**表'):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(stripped)
    elif stripped.startswith('[') and stripped.endswith(']'):
        # reference list entry
        p = doc.add_paragraph()
        p.add_run(stripped)
    else:
        p = doc.add_paragraph()
        # Preserve indentation for Chinese paragraph spacing
        if stripped.startswith('　'):
            p.add_run(stripped.lstrip('　'))
        else:
            p.add_run(stripped)

# Save document
doc.save(output_path)
print(f'已生成: {output_path}')
