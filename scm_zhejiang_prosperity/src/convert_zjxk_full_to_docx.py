#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将《浙江学刊》格式的完整版论文转换为Word文档
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
    for edge in ('top', 'left', 'bottom', 'right'):
        if edge in kwargs:
            edge_element = OxmlElement(f'w:{edge}')
            edge_element.set(qn('w:val'), kwargs[edge].get('val', 'single'))
            edge_element.set(qn('w:sz'), str(kwargs[edge].get('sz', 4)))
            edge_element.set(qn('w:color'), kwargs[edge].get('color', '000000'))
            tcBorders.append(edge_element)
    tcPr.append(tcBorders)


def convert_to_docx(md_path, docx_path):
    """将Markdown文件转换为Word文档（浙江学刊格式）"""
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建文档
    doc = Document()
    
    # 设置页面格式（A4）
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(3)
    
    # 设置默认字体
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
        
        # 主标题（# 开头，不是##）
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
        
        # 副标题（## —— 开头）
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
        
        # 一级标题（## 一、二、三...）
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
        
        # 二级标题（### （一）（二）...）
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
        
        # 表格处理
        if line.startswith('|'):
            if not in_table:
                in_table = True
                table_rows = []
            
            # 跳过分隔行
            if re.match(r'^\|[-:\s|]+\|$', line):
                i += 1
                continue
            
            # 解析表格行
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            table_rows.append(cells)
            i += 1
            continue
        else:
            # 表格结束，创建Word表格
            if in_table and table_rows:
                if len(table_rows) > 0 and len(table_rows[0]) > 0:
                    table = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
                    table.alignment = WD_TABLE_ALIGNMENT.CENTER
                    
                    for row_idx, row_data in enumerate(table_rows):
                        for col_idx, cell_text in enumerate(row_data):
                            if col_idx < len(table.rows[row_idx].cells):
                                cell = table.rows[row_idx].cells[col_idx]
                                cell.text = cell_text
                                
                                # 设置单元格格式
                                for para in cell.paragraphs:
                                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    for run in para.runs:
                                        run.font.name = '宋体'
                                        run.font.size = Pt(9)
                                        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                                        # 表头加粗
                                        if row_idx == 0:
                                            run.bold = True
                                
                                # 设置边框
                                border_props = {'val': 'single', 'sz': 4, 'color': '000000'}
                                set_cell_border(cell, top=border_props, bottom=border_props, 
                                              left=border_props, right=border_props)
                    
                    doc.add_paragraph()  # 表格后空行
                
                in_table = False
                table_rows = []
        
        # 粗体段落（**开头）
        if line.startswith('**') and '**' in line[2:]:
            # 查找完整的粗体内容
            bold_match = re.match(r'\*\*(.+?)\*\*(.*)$', line)
            if bold_match:
                p = doc.add_paragraph()
                # 首行缩进
                p.paragraph_format.first_line_indent = Cm(0.74)
                
                # 添加粗体部分
                bold_text = bold_match.group(1)
                run = p.add_run(bold_text)
                run.font.name = '宋体'
                run.font.size = Pt(10.5)
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                run.bold = True
                
                # 添加非粗体部分
                rest_text = bold_match.group(2)
                if rest_text:
                    run = p.add_run(rest_text)
                    run.font.name = '宋体'
                    run.font.size = Pt(10.5)
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                
                i += 1
                continue
        
        # 普通段落
        if line.strip():
            # 跳过图片占位符
            if line.strip().startswith('[图') or line.strip().startswith('**[图'):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(line.strip().replace('**', ''))
                run.font.name = '宋体'
                run.font.size = Pt(10)
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                i += 1
                continue
            
            # 处理公式（简化处理，保留原文本）
            if line.strip().startswith('$$'):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                formula_text = line.strip()
                run = p.add_run(formula_text)
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10.5)
                i += 1
                continue
            
            p = doc.add_paragraph()
            
            # 判断是否需要首行缩进
            # 摘要、关键词、作者信息等不缩进
            no_indent_prefixes = ['【', '**【', '**Abstract', '**Keywords', '（', 
                                  '**[', '[', '注：', '**表', '表', '图']
            should_indent = not any(line.strip().startswith(prefix) for prefix in no_indent_prefixes)
            
            if should_indent:
                p.paragraph_format.first_line_indent = Cm(0.74)  # 两个字符缩进
            
            # 处理行内粗体
            parts = re.split(r'(\*\*[^*]+\*\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    text = part[2:-2]
                    run = p.add_run(text)
                    run.font.name = '宋体'
                    run.font.size = Pt(10.5)
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                    run.bold = True
                else:
                    run = p.add_run(part)
                    run.font.name = '宋体'
                    run.font.size = Pt(10.5)
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        
        i += 1
    
    # 保存文档
    doc.save(docx_path)
    print(f"Word文档已保存: {docx_path}")
    return docx_path


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).parent.parent
    md_path = PROJECT_ROOT / "paper" / "论文_浙江学刊版_完整.md"
    docx_path = PROJECT_ROOT / "paper" / "论文_浙江学刊版_完整.docx"
    
    if md_path.exists():
        convert_to_docx(md_path, docx_path)
    else:
        print(f"文件不存在: {md_path}")
