#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Backend FastAPI para Gerador de Slides da Missa
Reutiliza a lógica existente (gerar_missa.py, banco.py)
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import logging

from servicos import gerar_missa, banco, converter_docx

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Slide Missa API",
    description="Gerador de slides para missa católica",
    version="1.0.0"
)

# CORS - permite acesso do frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, usar ["https://seu-dominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar banco
banco.inicializar()


# ============================================================================
# Rotas: Gerar Apresentação
# ============================================================================

@app.post("/api/gerar")
async def gerar_apresentacao(
    txt: UploadFile = File(...),
    pptx: UploadFile = File(...),
    nome_saida: str = "missa_pronta"
):
    """
    Gera apresentação PPTX a partir de TXT + PPTX base.
    
    - txt: arquivo .txt com cantos
    - pptx: arquivo .pptx ritual base
    - nome_saida: nome do arquivo de saída (sem extensão)
    """
    txt_temp = None
    pptx_temp = None
    output_temp = None
    
    try:
        # Validar tipos de arquivo
        if not txt.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Arquivo TXT obrigatório")
        if not pptx.filename.endswith('.pptx'):
            raise HTTPException(status_code=400, detail="Arquivo PPTX obrigatório")
        
        # Criar arquivos temporários
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            txt_temp = f.name
            f.write(await txt.read())
        
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            pptx_temp = f.name
            f.write(await pptx.read())
        
        output_temp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False).name
        
        # Gerar apresentação (reutiliza função existente)
        def log_func(msg):
            logger.info(msg)
        
        ok, msg = gerar_missa.gerar(txt_temp, pptx_temp, output_temp, log=log_func)
        
        if not ok:
            raise HTTPException(status_code=400, detail=f"Erro ao gerar: {msg}")
        
        # Preparar nome de saída
        if not nome_saida.endswith('.pptx'):
            nome_saida += '.pptx'
        
        # Retornar arquivo
        return FileResponse(
            path=output_temp,
            filename=nome_saida,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            headers={"Content-Disposition": f"attachment; filename={nome_saida}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na geração: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Limpeza de temporários seria aqui, mas FileResponse precisa do arquivo
        # Em produção, usar background task
        pass


# ============================================================================
# Rotas: Conversor DOCX → TXT
# ============================================================================

@app.post("/api/converter-docx")
async def converter_docx_endpoint(docx: UploadFile = File(...)):
    """
    Converte DOCX para TXT no formato esperado.

    - docx: arquivo .docx com cantos
    Retorna arquivo .txt para download
    """
    docx_temp = None
    txt_temp = None

    try:
        if not docx.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Arquivo DOCX obrigatório")

        # Criar arquivo temporário DOCX
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_temp = f.name
            f.write(await docx.read())

        # Converter
        txt_content = converter_docx.convert_docx_to_txt(docx_temp)

        # Preparar nome de saída
        nome_saida = docx.filename.replace('.docx', '.txt')

        # Criar arquivo TXT temporário para download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            txt_temp = f.name
            f.write(txt_content)

        return FileResponse(
            path=txt_temp,
            filename=nome_saida,
            media_type='text/plain; charset=utf-8',
            headers={"Content-Disposition": f"attachment; filename={nome_saida}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao converter DOCX: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao converter DOCX: {str(e)}")


# ============================================================================
# Rotas: Banco de Cantos
# ============================================================================

@app.get("/api/banco/posicoes")
async def get_posicoes():
    """Retorna lista de posições (filtros) disponíveis no banco."""
    try:
        posicoes = banco.buscar_posicoes()
        return {"posicoes": posicoes or []}
    except Exception as e:
        logger.error(f"Erro ao buscar posições: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banco/listar")
async def listar_banco(posicao: str = None):
    """
    Lista cantos do banco.
    - posicao: filtro opcional (ex: "CANTO DE ENTRADA")
    """
    try:
        if posicao and posicao != "Todas":
            cantos = banco.buscar_por_posicao(posicao)
        else:
            cantos = banco.buscar_todos()
        
        return {"cantos": cantos or []}
    except Exception as e:
        logger.error(f"Erro ao listar banco: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gerar-do-banco")
async def gerar_do_banco(
    pptx: UploadFile = File(...),
    chaves: list[str] = None,  # lista de chaves de cantos selecionados
    nome_saida: str = "missa_pronta"
):
    """
    Gera apresentação usando cantos salvos do banco + PPTX base.
    
    - pptx: arquivo .pptx ritual base
    - chaves: lista de chaves de cantos (ex: ["CANTO DE ENTRADA — Eu venho"])
    - nome_saida: nome do arquivo de saída
    """
    pptx_temp = None
    output_temp = None
    
    try:
        if not pptx.filename.endswith('.pptx'):
            raise HTTPException(status_code=400, detail="Arquivo PPTX obrigatório")
        
        if not chaves:
            raise HTTPException(status_code=400, detail="Selecione pelo menos um canto")
        
        # Criar PPTX temporário
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            pptx_temp = f.name
            f.write(await pptx.read())
        
        output_temp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False).name
        
        # Gerar (reutiliza função existente)
        def log_func(msg):
            logger.info(msg)
        
        ok, msg = gerar_missa.gerar_do_banco(pptx_temp, chaves, output_temp, log=log_func)
        
        if not ok:
            raise HTTPException(status_code=400, detail=f"Erro ao gerar: {msg}")
        
        if not nome_saida.endswith('.pptx'):
            nome_saida += '.pptx'
        
        return FileResponse(
            path=output_temp,
            filename=nome_saida,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            headers={"Content-Disposition": f"attachment; filename={nome_saida}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na geração do banco: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/banco/{canto_id}")
async def deletar_canto(canto_id: int):
    """Remove um canto do banco pelo ID."""
    try:
        banco.deletar(canto_id)
        return {"message": "Canto deletado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao deletar canto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
