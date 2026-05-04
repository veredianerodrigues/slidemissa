#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_missa.py - Logica de geracao de slides da Missa Catolica
"""

import re
import math
import unicodedata
from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from docx import Document
from docx.oxml.ns import qn as _qn
from pptx.oxml.ns import qn as _pptx_qn


# -- Constantes ---------------------------------------------------------------

TEXT_COLOR = RGBColor(0x00, 0x00, 0x00)
BG_COLOR   = RGBColor(0xFF, 0xFF, 0xFF)

BOX_LEFT_CM   = 0.0
BOX_TOP_CM    = 0.0
BOX_WIDTH_CM  = 25.4
BOX_HEIGHT_CM = 19.05

FONT_NAME = "Verdana"
MAX_LINES_PER_SLIDE = 8
FIXED_FONT_SIZE = 55
HEADER_RE    = re.compile(r'^\[(.+)\]\s*$')
BRACKET_RE   = re.compile(r'\[([^\]]+)\]')

TITLE_ALIASES = {
    'gloria': 'hino de louvor',
    'glória': 'hino de louvor',
    'canto final': 'final',
}

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


def normalize(text):
    text = text.lower()
    text = re.sub(r'\bcanto\s+(?:de|da|do|d[oa]s?)\s+', '', text)

    for alias, canonical in TITLE_ALIASES.items():
        text = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, text)

    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return re.sub(r'[\[\]\s]+', ' ', text).strip()


def _normalize_kw(text):
    text = text.lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def _para_is_bold(para):
    """Detecta negrito via runs explícitos ou hierarquia de estilos do parágrafo."""
    runs = para.runs
    if not runs:
        return False
    bold_votes = 0
    for run in runs:
        if run.bold is True:
            bold_votes += 1
        elif run.bold is None:
            # Negrito não definido no run — verifica a hierarquia de estilos
            try:
                style = para.style
                while style:
                    if style.font.bold is True:
                        bold_votes += 1
                        break
                    style = style.base_style
            except Exception:
                pass
    return bold_votes > len(runs) / 2


def _match_keyword(text_norm):
    for title, keywords in KEYWORDS_MAP.items():
        for kw in keywords:
            if _normalize_kw(kw) in text_norm:
                return title
    return None


def _is_section_title(line):
    """Linha de título: curta (<= 60 chars), toda em maiúsculas OU contém keyword conhecida."""
    line = line.lstrip('* ').strip()
    if not line or len(line) > 60:
        return False
    if line.upper() == line and len(line) > 4 and any(c.isalpha() for c in line):
        return True
    if not any(c in line for c in '.!?,') and _match_keyword(_normalize_kw(line)):
        return True
    return False


def _extrair_secoes_docx(doc):
    """Lê parágrafos do Document e retorna lista de seções brutas com metadados."""
    raw_lines = []
    for para in doc.paragraphs:
        full_text = para.text
        if not full_text.strip():
            raw_lines.append('')
            continue
        is_bold = _para_is_bold(para)
        for sub in full_text.split('\n'):
            text = sub.strip()
            if text:
                raw_lines.append(f'* {text}' if is_bold else text)

    blocks = []
    current = []
    for line in raw_lines:
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)

    title_positions = []
    for i, block in enumerate(blocks):
        if len(block) == 1 and _is_section_title(block[0]):
            raw = block[0].lstrip('* ').strip()
            matched = _match_keyword(_normalize_kw(raw))
            title_positions.append((i, raw, matched))

    sections_raw = []
    for idx, (pos, raw_title, matched_title) in enumerate(title_positions):
        next_pos = title_positions[idx + 1][0] if idx + 1 < len(title_positions) else len(blocks)
        content_blocks = blocks[pos + 1:next_pos]
        all_lines = []
        for cb in content_blocks:
            all_lines.extend(cb)
        title = matched_title if matched_title else raw_title
        sections_raw.append({
            'title': title,
            'titulo_original': raw_title,
            'lines': all_lines,
            'auto': not matched_title,
        })

    if 6 <= len(sections_raw) <= len(TITULOS_PADRAO):
        for i, s in enumerate(sections_raw):
            if s['auto']:
                s['title'] = TITULOS_PADRAO[i]

    return sections_raw


def validar_docx(docx_path):
    """Valida o DOCX antes de gerar o PPTX. Retorna erros, avisos e resumo das seções."""
    try:
        doc = Document(docx_path)
        sections_raw = _extrair_secoes_docx(doc)
    except Exception as e:
        return {'valido': False, 'erros': [f'Não foi possível ler o arquivo: {e}'], 'avisos': [], 'secoes': []}

    erros = []
    avisos = []
    secoes_info = []

    if not sections_raw:
        erros.append(
            'Nenhuma seção (título) encontrada. '
            'Os títulos devem estar em letras MAIÚSCULAS (ex: CANTO DE ENTRADA).'
        )
        return {'valido': False, 'erros': erros, 'avisos': avisos, 'secoes': []}

    for s in sections_raw:
        title = s['title']
        raw_title = s['titulo_original']
        lines = s['lines']
        reconhecido = not s['auto']

        tem_conteudo = any(l.strip() for l in lines)
        tem_negrito = any(l.startswith('* ') for l in lines)
        total_linhas = sum(1 for l in lines if l.strip())

        secoes_info.append({
            'titulo': title,
            'titulo_original': raw_title,
            'titulo_reconhecido': reconhecido,
            'tem_conteudo': tem_conteudo,
            'tem_negrito': tem_negrito,
            'total_linhas': total_linhas,
        })

        if not tem_conteudo:
            erros.append(f'Seção "{raw_title}" está vazia — nenhum conteúdo encontrado após o título.')
        else:
            if not tem_negrito:
                avisos.append(
                    f'Seção "{title}" não tem texto em negrito. '
                    'Refrões devem estar em negrito (selecione e pressione Ctrl+B).'
                )
            if not reconhecido:
                avisos.append(
                    f'Título "{raw_title}" não é um título litúrgico padrão — '
                    'verifique se está escrito corretamente.'
                )

    return {
        'valido': len(erros) == 0,
        'erros': erros,
        'avisos': avisos,
        'secoes': secoes_info,
    }


def parse_docx(docx_path, log=None):
    """Lê um DOCX e retorna seções no mesmo formato que parse_txt() retornava."""
    doc = Document(docx_path)
    sections_raw = _extrair_secoes_docx(doc)  # já aplica mapeamento posicional

    # Converte para o formato interno de blocos usado pelo gerador
    sections = {}
    for s in sections_raw:
        title = s['title']
        key = normalize(title)
        line_dicts = []
        for line in s['lines']:
            stripped = line.strip()
            if not stripped:
                continue
            is_bold = stripped.startswith('* ')
            text = stripped[2:] if is_bold else stripped
            if text:
                line_dicts.append({'text': text, 'bold': is_bold})

        blocos = []
        for sub in split_block(line_dicts):
            blocos.append(sub)

        expanded = []
        for block in blocos:
            expanded.extend(auto_split_large(block, 48))

        if expanded:
            sections[key] = {'titulo': title, 'blocos': expanded}

    if log:
        log('Secoes encontradas: ' + str(len(sections)))
        for key, data in sections.items():
            log('  [' + data['titulo'] + ']: ' + str(len(data['blocos'])) + ' slide(s)')

    return sections


def split_block(block_lines):
    if not block_lines:
        return []
    n = len(block_lines)

    if n >= 2 and n % 2 == 0:
        is_alt = all(
            not block_lines[i]['bold'] and block_lines[i + 1]['bold']
            for i in range(0, n, 2)
        )
        if is_alt:
            return [
                {'lines': [block_lines[i]['text'], block_lines[i + 1]['text']],
                 'bold': False}
                for i in range(0, n, 2)
            ]

    first_change = next(
        (i for i in range(1, n)
         if block_lines[i]['bold'] != block_lines[i - 1]['bold']),
        None
    )
    if first_change is not None:
        g1 = block_lines[:first_change]
        g2 = block_lines[first_change:]
        if len({l['bold'] for l in g1}) == 1 and len({l['bold'] for l in g2}) == 1:
            return [
                {'lines': [l['text'] for l in g1], 'bold': g1[0]['bold']},
                {'lines': [l['text'] for l in g2], 'bold': g2[0]['bold']},
            ]

    bold_majority = sum(1 for l in block_lines if l['bold']) > n / 2
    return [{'lines': [l['text'] for l in block_lines], 'bold': bold_majority}]


def estimate_lines_needed(text_lines, font_size_pt, bold=False, box_width_cm=BOX_WIDTH_CM):
    box_width_emu  = box_width_cm * 360000
    char_width_factor = 0.65 if bold else 0.60
    avg_char_w_emu = font_size_pt * char_width_factor * 12700
    chars_per_line = box_width_emu / avg_char_w_emu
    return sum(max(1, math.ceil(len(ln) / chars_per_line)) for ln in text_lines)


def estimate_max_lines(font_size_pt, box_height_cm=BOX_HEIGHT_CM):
    box_height_emu  = box_height_cm * 360000
    line_height_emu = font_size_pt * 1.25 * 12700
    return int(box_height_emu / line_height_emu)


def auto_split_large(block, font_min, box_width_cm=BOX_WIDTH_CM, box_height_cm=BOX_HEIGHT_CM):
    lines = block['lines']
    n = len(lines)

    if n == 0:
        return []

    font_est = FIXED_FONT_SIZE if FIXED_FONT_SIZE else font_min
    is_bold = block.get('bold', False)
    max_lines = estimate_max_lines(font_est, box_height_cm=box_height_cm)

    # Linha única longa: divide por palavras se não couber no slide
    if n == 1:
        if estimate_lines_needed(lines, font_est, bold=is_bold, box_width_cm=box_width_cm) <= max_lines:
            return [block]
        words = lines[0].split()
        if len(words) <= 1:
            return [block]
        mid = math.ceil(len(words) / 2)
        left  = {'lines': [' '.join(words[:mid])], 'bold': is_bold}
        right = {'lines': [' '.join(words[mid:])], 'bold': is_bold}
        return (auto_split_large(left, font_min, box_width_cm, box_height_cm) +
                auto_split_large(right, font_min, box_width_cm, box_height_cm))

    if n <= MAX_LINES_PER_SLIDE and estimate_lines_needed(lines, font_est, bold=is_bold, box_width_cm=box_width_cm) <= max_lines:
        return [block]

    mid = math.ceil(n / 2)
    left  = {'lines': lines[:mid], 'bold': block['bold']}
    right = {'lines': lines[mid:], 'bold': block['bold']}
    return auto_split_large(left, font_min, box_width_cm, box_height_cm) + auto_split_large(right, font_min, box_width_cm, box_height_cm)


def slide_full_text(slide):
    parts = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                t = para.text.strip()
                if t:
                    parts.append(t)
    return ' '.join(parts)


def slide_normalized_key(slide):
    txt = slide_full_text(slide).strip()
    if not txt or len(txt) > 80:
        return None
    clean = re.sub(r'\s*\|\s*', ' ', txt).strip()
    return normalize(clean)


def get_bg_color(slide):
    try:
        fill = slide.background.fill
        if fill.type is not None:
            return fill.fore_color.rgb
    except Exception:
        pass
    return BG_COLOR


def detect_slide_format(prs):
    slide_width_cm  = prs.slide_width  / 360000
    slide_height_cm = prs.slide_height / 360000
    return slide_width_cm, slide_height_cm


def choose_font_size(text_lines, font_min=48, font_max=60, box_width_cm=BOX_WIDTH_CM, box_height_cm=BOX_HEIGHT_CM):
    for size in range(font_max, font_min - 2, -2):
        if estimate_lines_needed(text_lines, size, box_width_cm=box_width_cm) <= estimate_max_lines(size, box_height_cm=box_height_cm):
            return size
    return font_min


def create_song_slide(prs, block, bg_color, box_width_cm, box_height_cm, font_min=48, font_max=60, fixed_font_size=None):
    lines     = block['lines']
    is_bold   = block['bold']
    font_size = fixed_font_size if fixed_font_size else choose_font_size(lines, font_min, font_max, box_width_cm, box_height_cm)

    slide = prs.slides.add_slide(prs.slide_layouts[6])

    for shape in list(slide.shapes):
        if shape.is_placeholder or (hasattr(shape, 'text') and not shape.text.strip()):
            sp = shape.element
            sp.getparent().remove(sp)

    fill  = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg_color

    txBox = slide.shapes.add_textbox(
        Cm(BOX_LEFT_CM), Cm(BOX_TOP_CM),
        Cm(box_width_cm), Cm(box_height_cm)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    body_pr = tf._txBody.find(_pptx_qn('a:bodyPr'))
    if body_pr is not None:
        body_pr.set('anchor', 'ctr')

    for i, line in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = PP_ALIGN.CENTER
        run = para.add_run()
        run.text           = line
        run.font.name      = FONT_NAME
        run.font.size      = Pt(font_size)
        run.font.bold      = is_bold
        run.font.color.rgb = TEXT_COLOR

    return slide


def move_slide(prs, from_idx, to_idx):
    if from_idx == to_idx:
        return
    sldIdLst = prs.slides._sldIdLst
    all_ids  = list(sldIdLst)
    sldId    = all_ids.pop(from_idx)
    all_ids.insert(to_idx, sldId)
    for el in list(sldIdLst):
        sldIdLst.remove(el)
    for el in all_ids:
        sldIdLst.append(el)


def gerar(docx_path, pptx_path, output_path, fonte_min=48, fonte_max=60, log=None):
    if log is None:
        log = lambda msg: None

    try:
        log('Lendo cantos: ' + docx_path)
        cantos = parse_docx(docx_path, log)

        log('Carregando ritual: ' + pptx_path)
        prs = Presentation(pptx_path)
        log('Total de slides: ' + str(len(prs.slides)))

        placeholders = []
        for i, slide in enumerate(prs.slides):
            key = slide_normalized_key(slide)
            if key and key in cantos:
                placeholders.append((i, key))
                log('  Slide ' + str(i + 1).zfill(2) + ': [' + cantos[key]['titulo'] + ']')

        if not placeholders:
            return False, 'Nenhum titulo do DOCX foi encontrado no PPTX.'

        box_width, box_height = detect_slide_format(prs)
        log(f'Dimensões do slide: {box_width:.2f} x {box_height:.2f} cm')

        total_inserted = 0
        for ph_idx, sec_key in reversed(placeholders):
            data     = cantos[sec_key]
            blocos   = data['blocos']
            bg_color = get_bg_color(prs.slides[ph_idx])
            log('Inserindo ' + str(len(blocos)) + ' slide(s) para [' + data['titulo'] + ']')
            slide_idx = 0
            for j, block in enumerate(blocos):
                sub_blocos = auto_split_large(block, fonte_min, box_width, box_height)
                for sub_block in sub_blocos:
                    create_song_slide(prs, sub_block, bg_color, box_width, box_height, fonte_min, fonte_max, fixed_font_size=FIXED_FONT_SIZE)
                    move_slide(prs, len(prs.slides) - 1, ph_idx + 1 + slide_idx)
                    slide_idx += 1
            total_inserted += slide_idx

        prs.save(output_path)
        msg = str(total_inserted) + ' slides inseridos. Total final: ' + str(len(prs.slides)) + ' slides.'
        log(msg)
        return True, msg

    except Exception as e:
        return False, 'Erro: ' + str(e)
