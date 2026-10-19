# -*- coding: utf-8 -*-
"""
layout_letra.py - Quebra de linhas e divisão de slides das letras dos cantos

Regras:
- Largura medida pela largura real do Verdana, com margem de segurança de 7%.
- Quebra balanceada, sem palavra solta na última linha e sem terminar linha em
  palavra fraca (a, o, de, que, me, com...).
- Máximo de MAX_LINHAS linhas visuais por slide; acima disso divide no fim de
  um verso, perto do meio, preferindo depois de pontuação ou onde o refrão recomeça.
- Estrofe (sem negrito) e refrão (negrito) nunca ficam no mesmo slide.
- Repetições curtas em slides seguidos (Amém! / Amém!) são juntadas até 3 linhas.
- "(2x)", "(3x)" e "(Bis)" ficam sempre na linha do verso.
"""

import re
import unicodedata

from .larguras_verdana import VERDANA, VERDANA_BOLD

MAX_LINHAS = 6
MAX_LINHAS_REPETICAO = 3
MARGEM_SEGURANCA = 0.07
INSET_PT = 7.2  # margem interna padrão da caixa de texto (0,1 polegada de cada lado)
PT_POR_CM = 72 / 2.54

PALAVRAS_FRACAS = {
    'a', 'o', 'as', 'os', 'e', 'ao', 'aos', 'à', 'às', 'um', 'uma',
    'de', 'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'em', 'num', 'numa',
    'que', 'me', 'te', 'se', 'lhe', 'meu', 'minha', 'teu', 'tua', 'seu', 'sua',
    'com', 'por', 'pra', 'pro', 'para', 'pelo', 'pela', 'nem', 'mas', 'ou',
}

REPETICAO_RE = re.compile(r'^\((?:\d+\s*x|bis)\)$', re.IGNORECASE)
PONTUACAO_FINAL = tuple('.,;:!?…')

# Custos da quebra de linha (a folga de cada linha custa no máximo 1)
CUSTO_LINHA_EXTRA = 1.0
CUSTO_PALAVRA_FRACA = 0.5
CUSTO_PALAVRA_SOLTA = 2.0
BONUS_PONTUACAO = 0.15
CUSTO_ESTOURO = 100.0


def largura_util_pt(box_width_cm):
    return (box_width_cm * PT_POR_CM - 2 * INSET_PT) * (1 - MARGEM_SEGURANCA)


def largura_pt(texto, bold, tamanho_pt):
    tabela = VERDANA_BOLD if bold else VERDANA
    media = tabela['n']
    return sum(tabela.get(c, media) for c in texto) * tamanho_pt / 1000


def _chave(texto):
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )
    return re.sub(r'[^\w]+', ' ', texto).strip()


def _palavras(texto):
    """Separa em palavras, grudando (2x)/(Bis) na palavra anterior."""
    palavras = []
    for p in texto.split():
        if palavras and REPETICAO_RE.match(p):
            palavras[-1] += ' ' + p
        else:
            palavras.append(p)
    return palavras


def _eh_fraca(palavra):
    # Palavra com pontuação ("que,") marca pausa e pode terminar a linha
    return palavra.lower() in PALAVRAS_FRACAS


def quebrar_verso(texto, bold, tamanho_pt, largura_max):
    """Quebra um verso em linhas visuais balanceadas."""
    palavras = _palavras(texto)
    if not palavras:
        return []
    m = len(palavras)
    larg_espaco = largura_pt(' ', bold, tamanho_pt)
    larg_palavras = [largura_pt(p, bold, tamanho_pt) for p in palavras]

    def custo_linha(i, j, ultima):
        w = sum(larg_palavras[i:j]) + larg_espaco * (j - i - 1)
        if w > largura_max:
            if j - i > 1:
                return None
            custo = CUSTO_ESTOURO  # palavra sozinha maior que a linha
        else:
            custo = ((largura_max - w) / largura_max) ** 2
        if not ultima and _eh_fraca(palavras[j - 1]):
            custo += CUSTO_PALAVRA_FRACA
        if not ultima and palavras[j - 1].endswith(PONTUACAO_FINAL):
            custo -= BONUS_PONTUACAO
        if ultima and j - i == 1 and m > 1:
            custo += CUSTO_PALAVRA_SOLTA
        return custo

    # melhor[k][j]: menor custo para as j primeiras palavras em k linhas
    inf = float('inf')
    melhor = [[inf] * (m + 1) for _ in range(m + 1)]
    corte = [[0] * (m + 1) for _ in range(m + 1)]
    melhor[0][0] = 0.0
    resultado = None
    for k in range(1, m + 1):
        for j in range(k, m + 1):
            for i in range(k - 1, j):
                if melhor[k - 1][i] == inf:
                    continue
                c = custo_linha(i, j, j == m)
                if c is None:
                    continue
                total = melhor[k - 1][i] + c
                if total < melhor[k][j]:
                    melhor[k][j] = total
                    corte[k][j] = i
        if melhor[k][m] < inf:
            total = melhor[k][m] + CUSTO_LINHA_EXTRA * k
            if resultado is None or total < resultado[0]:
                resultado = (total, k)
            elif k > resultado[1] + 1:
                break

    _, k = resultado
    linhas = []
    j = m
    while k > 0:
        i = corte[k][j]
        linhas.append(' '.join(palavras[i:j]))
        j, k = i, k - 1
    return linhas[::-1]


def _juntar_repeticoes_soltas(versos):
    """Uma linha só com "(2x)"/"(Bis)" vai para o fim do verso anterior."""
    resultado = []
    for v in versos:
        if resultado and REPETICAO_RE.match(v['text'].strip()):
            resultado[-1] = dict(resultado[-1], text=resultado[-1]['text'] + ' ' + v['text'].strip())
        else:
            resultado.append(dict(v))
    return resultado


def _separar_estrofe_refrao(versos):
    blocos = []
    for v in versos:
        if blocos and blocos[-1][-1]['bold'] == v['bold']:
            blocos[-1].append(v)
        else:
            blocos.append([v])
    return blocos


def _total_linhas(versos):
    return sum(len(v['linhas']) for v in versos)


def _slides_necessarios(n_linhas):
    return -(-n_linhas // MAX_LINHAS)


def _dividir(versos):
    total = _total_linhas(versos)
    if total <= MAX_LINHAS:
        return [versos]

    if len(versos) == 1:
        # Verso único maior que o slide: divide entre linhas visuais
        v = versos[0]
        partes = _slides_necessarios(total)
        tam = -(-total // partes)
        return [[dict(v, linhas=v['linhas'][i:i + tam])] for i in range(0, total, tam)]

    inicio_refrao = _chave(versos[0]['text'])
    melhor = None
    esquerda = 0
    for k in range(1, len(versos)):
        esquerda += len(versos[k - 1]['linhas'])
        direita = total - esquerda
        nota = abs(esquerda - total / 2)
        if versos[k - 1]['text'].rstrip().endswith(PONTUACAO_FINAL):
            nota -= 0.75
        if _chave(versos[k]['text']) == inicio_refrao:
            nota -= 1.0
        chave = (_slides_necessarios(esquerda) + _slides_necessarios(direita), nota)
        if melhor is None or chave < melhor[0]:
            melhor = (chave, k)

    k = melhor[1]
    return _dividir(versos[:k]) + _dividir(versos[k:])


def _eh_repeticao_curta(a, b):
    textos = {_chave(v['text']) for v in a + b}
    negritos = {v['bold'] for v in a + b}
    return (len(textos) == 1 and len(negritos) == 1
            and _total_linhas(a) + _total_linhas(b) <= MAX_LINHAS_REPETICAO)


def montar_slides(grupos, tamanho_pt, box_width_cm):
    """Converte os grupos de versos de um canto em slides.

    `grupos`: lista de grupos (separados por linha em branco no documento), cada um
    uma lista de {'text', 'bold'}. Retorna lista de slides, cada um uma lista de
    versos {'text', 'bold', 'linhas'}.
    """
    largura_max = largura_util_pt(box_width_cm)
    slides = []
    for grupo in grupos:
        for bloco in _separar_estrofe_refrao(_juntar_repeticoes_soltas(grupo)):
            versos = [
                dict(v, linhas=quebrar_verso(v['text'], v['bold'], tamanho_pt, largura_max))
                for v in bloco
            ]
            versos = [v for v in versos if v['linhas']]
            if versos:
                slides.extend(_dividir(versos))

    juntados = []
    for slide in slides:
        if juntados and _eh_repeticao_curta(juntados[-1], slide):
            juntados[-1] = juntados[-1] + slide
        else:
            juntados.append(slide)
    return juntados


def verificar_slides(slides, titulo):
    """Avisos da conferência final: excesso de linhas, palavra solta e slide de 1 linha."""
    avisos = []
    for n, slide in enumerate(slides, 1):
        total = _total_linhas(slide)
        if total > MAX_LINHAS:
            avisos.append(f'[{titulo}] slide {n}: {total} linhas (máximo {MAX_LINHAS}).')
        if total == 1:
            avisos.append(f'[{titulo}] slide {n}: só 1 linha ("{slide[0]["linhas"][0]}").')
        for v in slide:
            if len(v['linhas']) > 1 and len(_palavras(v['linhas'][-1])) == 1:
                avisos.append(f'[{titulo}] slide {n}: palavra solta na última linha ("{v["linhas"][-1]}").')
    return avisos
