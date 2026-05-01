#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_missa.py - Logica de geracao de slides da Missa Catolica
(Migrado do desktop para web)
"""

import re
import math
import unicodedata
from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# -- Constantes ---------------------------------------------------------------

TEXT_COLOR = RGBColor(0x00, 0x00, 0x00)
BG_COLOR   = RGBColor(0xFF, 0xFF, 0xFF)

BOX_LEFT_CM   = 0.0
BOX_TOP_CM    = 0.0
BOX_WIDTH_CM  = 25.4
BOX_HEIGHT_CM = 19.05

FONT_NAME = "Verdana"
MAX_LINES_PER_SLIDE = 8
FIXED_FONT_SIZE = 55  # Deixe None para automático, ou coloque um valor (ex: 55) para fixar
HEADER_RE    = re.compile(r'^\[(.+)\]\s*$')
BRACKET_RE   = re.compile(r'\[([^\]]+)\]')

TITLE_ALIASES = {
    'gloria': 'hino de louvor',
    'glória': 'hino de louvor',
    'canto final': 'final',
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


def parse_txt(txt_path, log=None):
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sections = {}
    current_key   = None
    current_title = None
    current_block = []

    def flush():
        if current_block and current_key is not None:
            for sub in split_block(current_block):
                sections[current_key]['blocos'].append(sub)
        current_block.clear()

    for raw in lines:
        line = raw.rstrip('\n').rstrip('\r')
        m = HEADER_RE.match(line.strip()) or BRACKET_RE.search(line)
        if m:
            flush()
            current_title = m.group(1).strip()
            current_key   = normalize(current_title)
            sections[current_key] = {'titulo': current_title, 'blocos': []}
            continue
        if not line.strip():
            flush()
            continue
        if current_key is not None:
            is_bold = line.startswith('*')
            text    = line.lstrip('* ').strip()
            if text:
                current_block.append({'text': text, 'bold': is_bold})

    flush()

    for key in sections:
        expanded = []
        for block in sections[key]['blocos']:
            expanded.extend(auto_split_large(block, 48))
        sections[key]['blocos'] = expanded

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


def estimate_lines_needed(text_lines, font_size_pt, bold=False):
    box_width_emu  = BOX_WIDTH_CM * 360000
    # Fatores calibrados para Verdana: bold ocupa ~8% mais que regular
    char_width_factor = 0.65 if bold else 0.60
    avg_char_w_emu = font_size_pt * char_width_factor * 12700
    chars_per_line = box_width_emu / avg_char_w_emu
    return sum(max(1, math.ceil(len(ln) / chars_per_line)) for ln in text_lines)


def estimate_max_lines(font_size_pt):
    box_height_emu  = BOX_HEIGHT_CM * 360000
    line_height_emu = font_size_pt * 1.25 * 12700
    return int(box_height_emu / line_height_emu)


def auto_split_large(block, font_min):
    lines = block['lines']
    n = len(lines)

    if n == 0:
        return []

    # Linha única não pode ser dividida
    if n == 1:
        return [block]

    font_est = FIXED_FONT_SIZE if FIXED_FONT_SIZE else font_min
    is_bold = block.get('bold', False)

    if n <= MAX_LINES_PER_SLIDE and estimate_lines_needed(lines, font_est, bold=is_bold) <= MAX_LINES_PER_SLIDE:
        return [block]

    mid = math.ceil(n / 2)

    left  = {'lines': lines[:mid], 'bold': block['bold']}
    right = {'lines': lines[mid:], 'bold': block['bold']}
    return auto_split_large(left, font_min) + auto_split_large(right, font_min)


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
    slide_width = prs.slide_width / 360000
    slide_height = prs.slide_height / 360000
    aspect_ratio = slide_width / slide_height
    
    if aspect_ratio > 1.5:
        return 25.4, 14.29
    else:
        return 25.4, 19.05


def choose_font_size(text_lines, font_min=48, font_max=60):
    for size in range(font_max, font_min - 2, -2):
        if estimate_lines_needed(text_lines, size) <= estimate_max_lines(size):
            return size
    return font_min


def create_song_slide(prs, block, bg_color, box_width_cm, box_height_cm, font_min=48, font_max=60, fixed_font_size=None):
    lines     = block['lines']
    is_bold   = block['bold']
    font_size = fixed_font_size if fixed_font_size else choose_font_size(lines, font_min, font_max)

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
    tf._txBody.set('anchor', 'ctr')

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


def gerar(txt_path, pptx_path, output_path, fonte_min=48, fonte_max=60, log=None):
    if log is None:
        log = lambda msg: None

    try:
        log('Lendo cantos: ' + txt_path)
        cantos = parse_txt(txt_path, log)

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
            return False, 'Nenhum titulo do TXT foi encontrado no PPTX.'

        box_width, box_height = detect_slide_format(prs)
        log('Formato do slide detectado: ' + ('4:3' if box_height > 14 else '16:9'))

        total_inserted = 0
        for ph_idx, sec_key in reversed(placeholders):
            data     = cantos[sec_key]
            blocos   = data['blocos']
            bg_color = get_bg_color(prs.slides[ph_idx])
            log('Inserindo ' + str(len(blocos)) + ' slide(s) para [' + data['titulo'] + ']')
            slide_idx = 0
            for j, block in enumerate(blocos):
                sub_blocos = auto_split_large(block, fonte_min)
                for sub_block in sub_blocos:
                    create_song_slide(prs, sub_block, bg_color, box_width, box_height, fonte_min, fonte_max, fixed_font_size=FIXED_FONT_SIZE)
                    move_slide(prs, len(prs.slides) - 1, ph_idx + 1 + slide_idx)
                    slide_idx += 1
            total_inserted += slide_idx

        prs.save(output_path)
        msg = str(total_inserted) + ' slides inseridos. Total final: ' + str(len(prs.slides)) + ' slides.'
        log(msg)

        # Salvar no banco automaticamente
        try:
            from . import banco
            salvos = 0
            for sec_key, data in cantos.items():
                if data['blocos']:
                    banco.salvar_canto(data['titulo'], data['blocos'])
                    salvos += 1
            if salvos:
                log(str(salvos) + ' canto(s) salvos no banco.')
        except Exception as e_banco:
            log('Aviso: nao foi possivel salvar no banco.')

        return True, msg

    except Exception as e:
        return False, 'Erro: ' + str(e)


def gerar_do_banco(pptx_path, chaves, output_path, fonte_min=48, fonte_max=60, log=None):
    """
    Gera slides usando cantos já cadastrados no banco.
    pptx_path: caminho do PPTX base
    chaves: lista de chaves de cantos (ex: ["CANTO DE ENTRADA — Eu venho"])
    """
    if log is None:
        log = lambda msg: None

    try:
        from . import banco
        
        log('Carregando ritual: ' + pptx_path)
        prs = Presentation(pptx_path)
        log('Total de slides: ' + str(len(prs.slides)))

        # Montar dicionário
        cantos = {}
        for chave in chaves:
            blocos = banco.carregar_blocos(chave)
            if blocos:
                # Extrair título a partir da chave (antes de " — ")
                titulo = chave.split(' — ')[0] if ' — ' in chave else chave
                key = normalize(titulo)
                cantos[key] = {'titulo': titulo, 'blocos': blocos}

        placeholders = []
        for i, slide in enumerate(prs.slides):
            key = slide_normalized_key(slide)
            if key and key in cantos:
                placeholders.append((i, key))
                log('  Slide ' + str(i + 1).zfill(2) + ': [' + cantos[key]['titulo'] + ']')

        if not placeholders:
            return False, 'Nenhum titulo dos cantos selecionados foi encontrado no PPTX.'

        box_width, box_height = detect_slide_format(prs)
        log('Formato do slide detectado: ' + ('4:3' if box_height > 14 else '16:9'))

        total_inserted = 0
        for ph_idx, sec_key in reversed(placeholders):
            data     = cantos[sec_key]
            blocos   = data['blocos']
            bg_color = get_bg_color(prs.slides[ph_idx])
            log('Inserindo ' + str(len(blocos)) + ' slide(s) para [' + data['titulo'] + ']')
            slide_idx = 0
            for j, block in enumerate(blocos):
                sub_blocos = auto_split_large(block, fonte_min)
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


def gerar_pptx_cantos_simples(chaves, output_path, fonte_min=48, fonte_max=60, log=None):
    """
    Gera um PPTX simples contendo apenas os cantos selecionados do banco.
    Sem ritual base - apenas os cantos.
    chaves: lista de chaves de cantos (ex: ["CANTO DE ENTRADA — Eu venho"])
    """
    if log is None:
        log = lambda msg: None

    try:
        from . import banco

        log('Criando apresentação simples com cantos...')
        prs = Presentation()
        prs.slide_width = Cm(25.4)
        prs.slide_height = Cm(19.05)

        log('Total de cantos: ' + str(len(chaves)))

        box_width = Cm(25.4)
        box_height = Cm(19.05)
        bg_color = BG_COLOR

        total_slides = 0
        for chave in chaves:
            blocos = banco.carregar_blocos(chave)
            if blocos:
                titulo = chave.split(' — ')[0] if ' — ' in chave else chave
                log('Adicionando ' + str(len(blocos)) + ' slide(s) para [' + titulo + ']')
                for block in blocos:
                    sub_blocos = auto_split_large(block, fonte_min)
                    for sub_block in sub_blocos:
                        create_song_slide(prs, sub_block, bg_color, box_width, box_height, fonte_min, fonte_max, fixed_font_size=FIXED_FONT_SIZE)
                        total_slides += 1

        prs.save(output_path)
        msg = str(total_slides) + ' slide(s) gerado(s) com sucesso.'
        log(msg)
        return True, msg

    except Exception as e:
        return False, 'Erro: ' + str(e)
