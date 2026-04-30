#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Backend FastAPI para Gerador de Slides da Missa
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import logging

from servicos import gerar_missa, banco, converter_docx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Slide Missa API",
    description="Gerador de slides para missa católica",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    txt_temp = None
    pptx_temp = None
    output_temp = None

    try:
        if not txt.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Arquivo TXT obrigatório")
        if not pptx.filename.endswith('.pptx'):
            raise HTTPException(status_code=400, detail="Arquivo PPTX obrigatório")

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            txt_temp = f.name
            f.write(await txt.read())

        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            pptx_temp = f.name
            f.write(await pptx.read())

        output_temp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False).name

        def log_func(msg):
            logger.info(msg)

        ok, msg = gerar_missa.gerar(txt_temp, pptx_temp, output_temp, log=log_func)

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
        logger.error(f"Erro na geração: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        pass


# ============================================================================
# Rotas: Conversor DOCX → TXT
# ============================================================================

@app.post("/api/converter-docx")
async def converter_docx_endpoint(docx: UploadFile = File(...)):
    docx_temp = None
    txt_temp = None

    try:
        if not docx.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Arquivo DOCX obrigatório")

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_temp = f.name
            f.write(await docx.read())

        txt_content = converter_docx.convert_docx_to_txt(docx_temp)
        nome_saida = docx.filename.replace('.docx', '.txt')

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


@app.post("/api/analisar-docx")
async def analisar_docx_endpoint(docx: UploadFile = File(...)):
    """Analisa DOCX e retorna seções detectadas com títulos mapeados."""
    docx_temp = None
    try:
        if not docx.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Arquivo DOCX obrigatório")

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_temp = f.name
            f.write(await docx.read())

        sections = converter_docx.analyze_docx(docx_temp)
        return {"sections": sections}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao analisar DOCX: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar DOCX: {str(e)}")
    finally:
        if docx_temp and os.path.exists(docx_temp):
            try:
                os.unlink(docx_temp)
            except Exception:
                pass


@app.get("/api/titulos-padrao")
async def get_titulos_padrao():
    """Retorna a lista canônica de títulos litúrgicos."""
    return {"titulos": converter_docx.TITULOS_PADRAO}


class MontarTxtRequest(BaseModel):
    sections: list[dict]


@app.post("/api/montar-txt")
async def montar_txt_endpoint(req: MontarTxtRequest):
    """Monta o TXT final a partir das seções (possivelmente editadas pelo usuário)."""
    try:
        txt = converter_docx.montar_txt(req.sections)
        return {"txt": txt}
    except Exception as e:
        logger.error(f"Erro ao montar TXT: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    """Lista cantos do banco. posicao: filtro opcional."""
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
    chaves: list[str] = None,
    nome_saida: str = "missa_pronta"
):
    pptx_temp = None
    output_temp = None

    try:
        if not pptx.filename.endswith('.pptx'):
            raise HTTPException(status_code=400, detail="Arquivo PPTX obrigatório")

        if not chaves:
            raise HTTPException(status_code=400, detail="Selecione pelo menos um canto")

        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            pptx_temp = f.name
            f.write(await pptx.read())

        output_temp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False).name

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


class DeletarVariosRequest(BaseModel):
    ids: list[int]


@app.post("/api/banco/deletar-varios")
async def deletar_varios_cantos(req: DeletarVariosRequest):
    """Remove múltiplos cantos pelos IDs em uma única operação."""
    try:
        if not req.ids:
            raise HTTPException(status_code=400, detail="Nenhum ID informado")
        deletados = banco.deletar_varios(req.ids)
        return {"deletados": deletados}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar cantos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/banco")
async def limpar_banco(confirmar: bool = Query(False)):
    """Remove todos os cantos do banco. Requer ?confirmar=true."""
    if not confirmar:
        raise HTTPException(
            status_code=400,
            detail="Operação destrutiva: passe ?confirmar=true para confirmar"
        )
    try:
        deletados = banco.limpar_todos()
        return {"message": "Banco de cantos limpo com sucesso", "deletados": deletados}
    except Exception as e:
        logger.error(f"Erro ao limpar banco: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class GerarPptxCantosRequest(BaseModel):
    chaves: list[str]
    nome_saida: str = "cantos"


@app.post("/api/gerar-pptx-cantos")
async def gerar_pptx_cantos(req: GerarPptxCantosRequest):
    output_temp = None
    try:
        if not req.chaves:
            raise HTTPException(status_code=400, detail="Selecione pelo menos um canto")

        output_temp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False).name

        def log_func(msg):
            logger.info(msg)

        ok, msg = gerar_missa.gerar_pptx_cantos_simples(req.chaves, output_temp, log=log_func)

        if not ok:
            raise HTTPException(status_code=400, detail=f"Erro ao gerar: {msg}")

        nome_saida = req.nome_saida
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
        logger.error(f"Erro na geração de cantos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
