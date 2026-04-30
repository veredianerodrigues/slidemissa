#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
converter_docx.py - Converte DOCX para TXT no formato esperado
"""

import re
from docx import Document
from docx.oxml.ns import qn


def extract_text_from_docx(docx_path):
    """Extrai texto do DOCX preservando formatação (negrito, títulos)"""
    doc = Document(docx_path)
    lines = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            lines.append("")
            continue

        # Detecta negrito: se a maioria dos runs está em negrito
        runs = para.runs
        if runs:
            bold_count = sum(1 for run in runs if run.bold)
            is_bold = bold_count > len(runs) / 2
        else:
            is_bold = False

        # Marca com asterisco se for negrito
        if is_bold and text:
            lines.append(f"* {text}")
        else:
            lines.append(text)

    return lines


def detect_titles(lines):
    """Detecta títulos baseado em heurísticas"""
    processed = []

    for i, line in enumerate(lines):
        if not line.strip():
            processed.append(line)
            continue

        # Heurísticas para detectar títulos:
        # 1. Linhas muito curtas (< 30 chars) no início de seções
        # 2. Linhas em MAIÚSCULAS
        # 3. Linhas que vêm após linhas em branco
        is_short = len(line) < 30
        is_all_caps = line.isupper() and len(line) > 3
        after_blank = i > 0 and not lines[i-1].strip()

        is_title = (is_short or is_all_caps) and after_blank

        if is_title and line.strip():
            # Remove asterisco se tiver (títulos não podem ser negrito)
            clean_title = line.lstrip('* ').strip()
            processed.append(f"[{clean_title}]")
        else:
            processed.append(line)

    return processed


def convert_docx_to_txt(docx_path, output_txt_path=None):
    """
    Converte DOCX para TXT no formato esperado
    Retorna o conteúdo como string se output_txt_path for None
    """
    try:
        # Extrai texto
        lines = extract_text_from_docx(docx_path)

        # Detecta títulos
        lines = detect_titles(lines)

        # Remove linhas em branco duplicadas
        cleaned = []
        last_blank = False
        for line in lines:
            if not line.strip():
                if not last_blank:
                    cleaned.append("")
                    last_blank = True
            else:
                cleaned.append(line)
                last_blank = False

        # Remove linhas em branco no início e final
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()

        content = '\n'.join(cleaned)

        # Salva se path foi fornecido
        if output_txt_path:
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    except Exception as e:
        raise ValueError(f"Erro ao converter DOCX: {str(e)}")
