#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Backend FastAPI para Gerador de Slides da Missa
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import logging

from servicos import gerar_missa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Slide Missa API",
    description="Gerador de slides para missa católica",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/gerar")
async def gerar_apresentacao(
    docx: UploadFile = File(...),
    pptx: UploadFile = File(...),
    nome_saida: str = "missa_pronta"
):
    docx_temp = None
    pptx_temp = None
    output_temp = None

    try:
        if not docx.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Arquivo DOCX obrigatório")
        if not pptx.filename.endswith('.pptx'):
            raise HTTPException(status_code=400, detail="Arquivo PPTX obrigatório")

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_temp = f.name
            f.write(await docx.read())

        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as f:
            pptx_temp = f.name
            f.write(await pptx.read())

        output_temp = tempfile.NamedTemporaryFile(suffix='.pptx', delete=False).name

        def log_func(msg):
            logger.info(msg)

        ok, msg = gerar_missa.gerar(docx_temp, pptx_temp, output_temp, log=log_func)

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
        for path in [docx_temp, pptx_temp]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
