#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
converter_docx.py - Converte DOCX para TXT no formato esperado
"""

import unicodedata
from docx import Document


TITULOS_PADRAO = [
    'CANTO DE ENTRADA',
    'CANTO DO ATO PENITENCIAL',
    'CANTO DO GLÓRIA',
    'CANTO DE ACLAMAÇÃO',
    'CANTO DO OFERTÓRIO',
    'SANTO',
    'CANTO DE COMUNHÃO',
    'CANTO FINAL',
]

KEYWORDS_MAP = {
    'CANTO DE ENTRADA': [
        'entrada', 'inicio', 'início', 'abertura', 'procissao', 'procissão', 'canto inicial'
    ],
    'CANTO DO ATO PENITENCIAL': [
        'penitencial', 'ato penitencial', 'canto penitencial'
    ],
    'CANTO DO GLÓRIA': [
        'gloria', 'glória', 'hino de louvor'
    ],
    'CANTO DE ACLAMAÇÃO': [
        'aclamacao', 'aclamação', 'evangelho'
    ],
    'CANTO DO OFERTÓRIO': [
        'ofertorio', 'ofertório', 'ofertas', 'apresentacao das oferendas', 'apresentação das oferendas'
    ],
    'SANTO': [
        'hosana', 'santo santo', 'santo, santo, santo'
    ],
    'CANTO DE COMUNHÃO': [
        'comunhao', 'comunhão', 'hino de comunhão'
    ],
    'CANTO FINAL': [
        'final', 'saida', 'saída', 'envio', 'despedida', 'canto final'
    ],
}

# Número mínimo de seções para aplicar mapeamento posicional automático
_MIN_SECOES_AUTO = 6


def _normalize(text):
    text = text.lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def _match_keyword(text_norm):
    for title, keywords in KEYWORDS_MAP.items():
        for kw in keywords:
            if _normalize(kw) in text_norm:
                return title
    return None


def extract_text_from_docx(docx_path):
    """
    Extrai texto do DOCX preservando negrito e quebras de linha suaves (<w:br/>).
    Cada parágrafo DOCX é separado por linha em branco, pois é uma unidade natural
    (verso, refrão ou título) — independente de o DOCX ter parágrafos em branco ou não.
    """
    doc = Document(docx_path)
    lines = []
    for para in doc.paragraphs:
        full_text = para.text  # \n presente quando o parágrafo contém soft returns
        if not full_text.strip():
            lines.append('')
            continue

        runs = para.runs
        if runs:
            bold_count = sum(1 for run in runs if run.bold)
            is_bold = bold_count > len(runs) / 2
        else:
            is_bold = False

        # Divide nos soft returns preservando as quebras naturais do DOCX
        sub_lines = full_text.split('\n')
        for sub in sub_lines:
            text = sub.strip()
            if text:
                lines.append(f'* {text}' if is_bold else text)
            else:
                lines.append('')

        # Garante separação entre parágrafos para que extract_sections
        # trate cada parágrafo como bloco independente
        lines.append('')

    return lines


def extract_sections(lines):
    """
    Agrupa linhas em blocos separados por linhas em branco.
    Todos os blocos são mantidos. Linhas em branco são removidas.
    """
    blocks = []
    current = []
    for line in lines:
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _is_section_title(block):
    """
    Bloco de título: linha única, curta (<= 60 chars),
    e que seja toda em maiúsculas com ao menos uma letra, OU contenha keyword conhecida.
    """
    if len(block) != 1:
        return False
    line = block[0].lstrip('* ').strip()
    if not line or len(line) > 60:
        return False
    if line.upper() == line and len(line) > 4 and any(c.isalpha() for c in line):
        return True
    # Títulos de seção não têm pontuação — rejeita letras de músicas
    if not any(c in line for c in '.!?,') and _match_keyword(_normalize(line)):
        return True
    return False


def auto_map_sections(blocks):
    """
    Identifica blocos de título e agrupa blocos de conteúdo sob cada seção.
    Retorna lista de {title, lines, confidence}.
    """
    title_positions = []
    for i, block in enumerate(blocks):
        if _is_section_title(block):
            raw = block[0].lstrip('* ').strip()
            matched = _match_keyword(_normalize(raw))
            title_positions.append((i, raw, matched))

    if not title_positions:
        return []

    sections = []
    for idx, (pos, raw_title, matched_title) in enumerate(title_positions):
        next_pos = title_positions[idx + 1][0] if idx + 1 < len(title_positions) else len(blocks)
        content_blocks = blocks[pos + 1:next_pos]

        all_lines = []
        for cb in content_blocks:
            all_lines.extend(cb)

        if matched_title:
            sections.append({'title': matched_title, 'lines': all_lines, 'confidence': 'keyword'})
        else:
            sections.append({'title': raw_title, 'lines': all_lines, 'confidence': 'unknown'})

    # Com 6 a 8 seções, mapeia as desconhecidas pela ordem litúrgica posicional
    if _MIN_SECOES_AUTO <= len(sections) <= len(TITULOS_PADRAO):
        for i, s in enumerate(sections):
            if s['confidence'] == 'unknown':
                s['title'] = TITULOS_PADRAO[i]
                s['confidence'] = 'auto'

    return sections


def analyze_docx(docx_path):
    """Analisa DOCX e retorna dados estruturados de seções."""
    lines = extract_text_from_docx(docx_path)
    blocks = extract_sections(lines)
    return auto_map_sections(blocks)



def montar_txt(sections):
    """
    Monta TXT: cabeçalho [TÍTULO] + linhas por seção.
    Quebras de linha do DOCX (soft returns) são preservadas.
    Linha em branco é inserida ao alternar entre verso (normal) e refrão (negrito).
    """
    parts = []
    for section in sections:
        title = section.get('title', '').strip()
        lines = section.get('lines', [])
        if not title or title == '—':
            continue
        parts.append(f'[{title}]')

        prev_bold = None
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            is_bold = stripped.startswith('* ')
            text = stripped[2:] if is_bold else stripped

            if prev_bold is not None and is_bold != prev_bold:
                parts.append('')

            parts.append(('* ' if is_bold else '') + text)
            prev_bold = is_bold

        parts.append('')
    return '\n'.join(parts).strip()


def convert_docx_to_txt(docx_path, output_txt_path=None):
    """Converte DOCX para TXT. Retorna string se output_txt_path for None."""
    try:
        sections = analyze_docx(docx_path)
        content = montar_txt(sections) if sections else ''

        if not content:
            lines = extract_text_from_docx(docx_path)
            cleaned, last_blank = [], False
            for line in lines:
                if not line.strip():
                    if not last_blank:
                        cleaned.append('')
                        last_blank = True
                else:
                    cleaned.append(line)
                    last_blank = False
            while cleaned and not cleaned[0].strip():
                cleaned.pop(0)
            while cleaned and not cleaned[-1].strip():
                cleaned.pop()
            content = '\n'.join(cleaned)

        if output_txt_path:
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return content

    except Exception as e:
        raise ValueError(f'Erro ao converter DOCX: {str(e)}')
