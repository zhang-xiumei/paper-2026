"""
将浙江学刊版论文转换为Word文档
按照《浙江学刊》格式要求排版
"""

from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path
import re

def set_cell_border(cell, **kwargs):
    """设置单元格边框"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ['top', 'left', 'bottom', 'right']:
        if edge in kwargs:
            edge_element = OxmlElement(f'w:{edge}')
            edge_element.set(qn('w:val'), kwargs[edge].get('val', 'single'))
            edge_element.set(qn('w:sz'), str(kwargs[edge].get('sz', 4)))
            edge_element.set(qn('w:color'), kwargs[edge].get('color', '000000'))
            tcBorders.append(edge_element)
    tcPr.append(tcBorders)

def convert_to_docx(md_path, docx_path):
    """转换Markdown为Word文档"""
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    doc = Document()
    
    # 设置页面
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(3)
    
    # 设置默认样式
    style = doc.styles['Normal']
    style.font.name = '宋体'
    style.font.size = Pt(10.5)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    
    lines = content.split('\n')
    i = 0
    in_table = False
    table_rows = []
    
    while i < len(lines):
        line = lines[i]
        
        # 跳过分隔线
        if line.strip() == '---':
            i += 1
            continue
        
        # 主标题
        if line.startswith('# ') and not line.startswith('## '):
            title = line[2:].strip()
            p = doc.add_paragraph()
            run = p.add_run(title)
            run.font.name = '黑体'
            run.font.size = Pt(18)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
            run.bold = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(6)
            i += 1
            continue
        
        # 副标题
        if line.startswith('## ——'):
            subtitle = line[5:].strip()
            p = doc.add_paragraph()
            run = p.add_run('——' + subtitle)
            run.font.name = '黑体'
            run.font.size = Pt(14)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(12)
            i += 1
            continue
        
        # 一级标题（一、二、三）
        if line.startswith('## ') and not line.startswith('## ——'):
            title = line[3:].strip()
            p = doc.add_paragraph()
            run = p.add_run(title)
            run.font.name = '黑体'
            run.font.size = Pt(12)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
            run.bold = True
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            i += 1
            continue
        
        # 二级标题（（一）（二））
        if line.startswith('### '):
            title = line[4:].strip()
            p = doc.add_paragraph()
            run = p.add_run(title)
            run.font.name = '楷体'
            run.font.size = Pt(11)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '楷体')
            run.bold = True
            p.paragraph_format.space_before = Pt(6)
            i += 1
            continue
        
        # 表格
        if line.startswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
            
            if '---' in line or ':-' in line or '-:' in line:
                i += 1
                continue
            
            cells = [c.strip() for c in line.split('|')[1:-1]]
            table_rows.append(cells)
            i += 1
            
            if i >= len(lines) or not lines[i].startswith('|'):
                if table_rows:
                    table = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    
                    for row_idx, row_data in enumerate(table_rows):
                        for col_idx, cell_data in enumerate(row_data):
                            cell = table.cell(row_idx, col_idx)
                            clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell_data)
                            cell.text = clean_text
                            
                            # 设置单元格格式
                            for para in cell.paragraphs:
                                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                for run in para.runs:
                                    run.font.size = Pt(9)
                                    run.font.name = '宋体'
                            
                            # 首行加粗
                            if row_idx == 0:
                                for para in cell.paragraphs:
                                    for run in para.runs:
                                        run.bold = True
                    
                    doc.add_paragraph()
                
                in_table = False
                table_rows = []
            continue
        
        # 粗体开头的段落
        if line.startswith('**') and '**' in line[2:]:
            p = doc.add_paragraph()
            
            # 解析粗体
            parts = re.split(r'(\*\*[^*]+\*\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                    run.font.name = '宋体'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                elif part.strip():
                    run = p.add_run(part)
                    run.font.name = '宋体'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            
            # 摘要、关键词等居中或首行缩进
            if line.startswith('**摘') or line.startswith('**关键词') or line.startswith('**中图'):
                p.paragraph_format.first_line_indent = Cm(0)
            elif line.startswith('**Abstract') or line.startswith('**Keywords'):
                p.paragraph_format.first_line_indent = Cm(0)
            else:
                p.paragraph_format.first_line_indent = Cm(0.74)
            
            i += 1
            continue
        
        # 普通段落
        if line.strip():
            p = doc.add_paragraph()
            
            # 处理脚注引用
            text = line
            text = re.sub(r'①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩|⑪|⑫', lambda m: m.group(), text)
            
            # 处理粗体
            parts = re.split(r'(\*\*[^*]+\*\*)', text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                else:
                    run = p.add_run(part)
                run.font.name = '宋体'
                run.font.size = Pt(10.5)
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            
            # 首行缩进
            p.paragraph_format.first_line_indent = Cm(0.74)
        
        i += 1
    
    doc.save(docx_path)
    print(f"Word文档已保存: {docx_path}")


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).parent.parent
    
    md_path = PROJECT_ROOT / "paper" / "论文_浙江学刊版.md"
    docx_path = PROJECT_ROOT / "paper" / "论文_浙江学刊版.docx"
    
    if md_path.exists():
        convert_to_docx(md_path, docx_path)
    else:
        print(f"文件不存在: {md_path}")
