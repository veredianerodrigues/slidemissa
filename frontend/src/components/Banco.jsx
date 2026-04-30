import { useState, useEffect, useRef } from 'react';
import { obterPosicoes, listarCantos, gerarDoBanco, deletarCanto, deletarVarios, gerarPptxCantos } from '../api';
import { useApi, downloadFile } from '../hooks/useApi';
import './Banco.css';

export default function Banco() {
  const [posicoes, setPosicoes] = useState([]);
  const [filtro, setFiltro] = useState('Todas');
  const [cantos, setCantos] = useState([]);
  const [selecionados, setSelecionados] = useState(new Set());
  const [expandido, setExpandido] = useState(new Set());
  const [pptxFile, setPptxFile] = useState(null);
  const [nomeSaida, setNomeSaida] = useState('missa_pronta');
  const [log, setLog] = useState([]);
  const [deletando, setDeletando] = useState(false);
  const [modalAberto, setModalAberto] = useState(false);
  const [mensagemModal, setMensagemModal] = useState('');
  const [acaoModal, setAcaoModal] = useState(null);
  const modalRef = useRef(null);
  const { call, loading, error, setError } = useApi();

  useEffect(() => {
    carregarDados();
  }, []);

  useEffect(() => {
    if (modalAberto && modalRef.current) {
      modalRef.current.focus();
    }
  }, [modalAberto]);

  const carregarDados = async () => {
    try {
      const pos = await call(obterPosicoes);
      setPosicoes(pos || []);
      await filtrarCantos(filtro || 'Todas');
    } catch (err) {
      console.error('Erro ao carregar:', err);
      setPosicoes([]);
      setCantos([]);
    }
  };

  const filtrarCantos = async (posicao) => {
    setFiltro(posicao);
    setSelecionados(new Set());
    try {
      const lista = await call(listarCantos, posicao);
      setCantos(lista || []);
    } catch (err) {
      console.error('Erro ao filtrar:', err);
      setCantos([]);
    }
  };

  const toggleSelecao = (cantoId) => {
    const novo = new Set(selecionados);
    if (novo.has(cantoId)) {
      novo.delete(cantoId);
    } else {
      novo.add(cantoId);
    }
    setSelecionados(novo);
  };

  const toggleExpandido = (cantoId) => {
    const novo = new Set(expandido);
    if (novo.has(cantoId)) {
      novo.delete(cantoId);
    } else {
      novo.add(cantoId);
    }
    setExpandido(novo);
  };

  const handleGerar = async (e) => {
    e.preventDefault();
    setLog([]);
    setError(null);

    if (selecionados.size === 0) {
      setError('Selecione pelo menos um canto');
      return;
    }
    if (!pptxFile) {
      setError('Selecione um arquivo .pptx');
      return;
    }

    try {
      setLog(prev => [...prev, `Gerando com ${selecionados.size} canto(s)...`]);
      const chavesSelecionadas = Array.from(selecionados)
        .map(id => cantos.find(c => c.id === id)?.chave)
        .filter(chave => chave);
      const blob = await call(gerarDoBanco, pptxFile, chavesSelecionadas, nomeSaida);
      setLog(prev => [...prev, '✓ Apresentação gerada com sucesso!']);

      const filename = nomeSaida.endsWith('.pptx') ? nomeSaida : nomeSaida + '.pptx';
      downloadFile(blob, filename);
    } catch (err) {
      setLog(prev => [...prev, '✗ Erro ao gerar']);
    }
  };

  const handleGerarPptxCantos = async () => {
    setLog([]);
    setError(null);

    if (selecionados.size === 0) {
      setError('Selecione pelo menos um canto');
      return;
    }

    try {
      setLog(prev => [...prev, `Gerando PPTX com ${selecionados.size} canto(s)...`]);
      const chavesSelecionadas = Array.from(selecionados)
        .map(id => cantos.find(c => c.id === id)?.chave)
        .filter(chave => chave);
      const blob = await call(gerarPptxCantos, chavesSelecionadas, nomeSaida);
      setLog(prev => [...prev, '✓ PPTX gerado com sucesso!']);

      const filename = nomeSaida.endsWith('.pptx') ? nomeSaida : nomeSaida + '.pptx';
      downloadFile(blob, filename);
    } catch (err) {
      setLog(prev => [...prev, '✗ Erro ao gerar PPTX']);
    }
  };

  const handleDeletar = (cantoId) => {
    setMensagemModal('Tem certeza que deseja deletar este canto?');
    setAcaoModal(() => async () => {
      setDeletando(true);
      try {
        await deletarCanto(cantoId);
        setModalAberto(false);
        await carregarDados();
      } catch (err) {
        const mensagemErro = err.response?.data?.detail || 'Erro ao deletar canto';
        setError(mensagemErro);
        setModalAberto(false);
      } finally {
        setDeletando(false);
      }
    });
    setModalAberto(true);
  };

  const handleDeletarSelecionados = () => {
    if (selecionados.size === 0) return;
    setMensagemModal(`Deletar ${selecionados.size} canto(s) selecionado(s)?`);
    setAcaoModal(() => async () => {
      setDeletando(true);
      try {
        setLog([`Deletando ${selecionados.size} canto(s)...`]);
        const ids = Array.from(selecionados);
        const { deletados } = await deletarVarios(ids);
        setLog([`✓ ${deletados} canto(s) deletado(s)!`]);
        setModalAberto(false);
        setSelecionados(new Set());
        await carregarDados();
      } catch (err) {
        const mensagemErro = err.response?.data?.detail || 'Erro ao deletar cantos';
        setLog([`✗ ${mensagemErro}`]);
        setModalAberto(false);
      } finally {
        setDeletando(false);
      }
    });
    setModalAberto(true);
  };

  const confirmarModal = async () => {
    if (acaoModal) {
      await acaoModal();
    }
  };

  const cancelarModal = () => {
    setModalAberto(false);
    setAcaoModal(null);
    setMensagemModal('');
  };

  const handleModalKeyDown = (e) => {
    if (e.key === 'Escape') cancelarModal();
  };

  return (
    <div className="banco-container">
      <div className="banco-header">
        <h2>Banco de Cantos</h2>
        <p>Reutilize cantos já cadastrados</p>
      </div>

      <div className="filtro-section">
        <label>Filtrar por posição:</label>
        <select value={filtro} onChange={(e) => filtrarCantos(e.target.value)}>
          <option value="Todas">Todas</option>
          {posicoes.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <button onClick={carregarDados} className="btn-refresh">
          Atualizar
        </button>
      </div>

      <div className="cantos-table">
        <div className="table-header">
          <div className="col-check">✓</div>
          <div className="col-posicao">Posição</div>
          <div className="col-canto">Canto</div>
          <div className="col-data">Cadastrado</div>
          <div className="col-acao">Ação</div>
        </div>
        <div className="table-body">
          {cantos.length === 0 ? (
            <div className="no-data">Nenhum canto encontrado</div>
          ) : (
            cantos.map(canto => (
              <div key={canto.chave} className="table-row-wrapper">
                <div className="table-row">
                  <div className="col-check">
                    <input
                      type="checkbox"
                      checked={selecionados.has(canto.id)}
                      onChange={() => toggleSelecao(canto.id)}
                    />
                  </div>
                  <div className="col-posicao">{canto.posicao}</div>
                  <div className="col-canto">{canto.nome}</div>
                  <div className="col-data">{canto.criado_em}</div>
                  <div className="col-acao">
                    <button
                      className="btn-preview"
                      onClick={() => toggleExpandido(canto.id)}
                      title={expandido.has(canto.id) ? 'Fechar' : 'Ver prévia'}
                    >
                      {expandido.has(canto.id) ? '▼' : '▶'}
                    </button>
                    <button
                      className="btn-delete"
                      onClick={() => handleDeletar(canto.id)}
                    >
                      Deletar
                    </button>
                  </div>
                </div>
                {expandido.has(canto.id) && (
                  <div className="preview-content">
                    {canto.blocos && canto.blocos.length > 0 ? (
                      <div className="preview-blocos">
                        {canto.blocos.slice(0, 3).map((bloco, idx) => (
                          <div key={idx} className="preview-bloco">
                            {Array.isArray(bloco.lines) ? bloco.lines.slice(0, 2).join(' · ') : bloco}
                          </div>
                        ))}
                        {canto.blocos.length > 3 && <div className="preview-more">... +{canto.blocos.length - 3} mais</div>}
                      </div>
                    ) : (
                      <div className="preview-empty">Sem conteúdo</div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="gerar-banco-section">
        <div className="form-group">
          <label>Ritual (.pptx)</label>
          <input
            type="file"
            accept=".pptx"
            onChange={(e) => setPptxFile(e.target.files[0])}
            disabled={loading}
          />
          {pptxFile && <span className="file-name">{pptxFile.name}</span>}
        </div>

        <div className="form-group">
          <label>Nome de saída</label>
          <div className="input-with-suffix">
            <input
              type="text"
              value={nomeSaida}
              onChange={(e) => setNomeSaida(e.target.value)}
              disabled={loading}
            />
            <span>.pptx</span>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="botoes-grupo">
          <button
            onClick={handleGerar}
            disabled={loading || selecionados.size === 0}
            className="btn-primary"
          >
            {loading ? 'Gerando...' : `Gerar com ${selecionados.size} selecionado(s)`}
          </button>
          <button
            onClick={handleDeletarSelecionados}
            disabled={deletando || selecionados.size === 0}
            className="btn-delete-mass"
          >
            {deletando ? 'Deletando...' : `Deletar ${selecionados.size} selecionado(s)`}
          </button>
        </div>

        <button
          onClick={handleGerarPptxCantos}
          disabled={loading || selecionados.size === 0}
          className="btn-pptx-simples"
        >
          {loading ? 'Gerando PPTX...' : `Gerar PPTX Simples (${selecionados.size} canto(s))`}
        </button>
      </div>

      {log.length > 0 && (
        <div className="log-container">
          <h3>Log</h3>
          <div className="log-content">
            {log.map((msg, idx) => (
              <div key={idx} className="log-line">{msg}</div>
            ))}
          </div>
        </div>
      )}

      {modalAberto && (
        <div
          className="modal-overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
          onKeyDown={handleModalKeyDown}
          onClick={cancelarModal}
        >
          <div
            className="modal-content"
            ref={modalRef}
            tabIndex={-1}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3 id="modal-title">Confirmar ação</h3>
            </div>
            <div className="modal-body">
              <p>{mensagemModal}</p>
            </div>
            <div className="modal-footer">
              <button onClick={cancelarModal} className="btn-modal-cancel" disabled={deletando}>
                Cancelar
              </button>
              <button onClick={confirmarModal} className="btn-modal-confirm" disabled={deletando}>
                {deletando ? 'Aguarde...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
