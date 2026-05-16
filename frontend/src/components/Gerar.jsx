import { useState } from 'react';
import { gerarApresentacao, gerarEditado, validarDocx } from '../api';
import { useApi, downloadFile } from '../hooks/useApi';
import ListaCantos from './ListaCantos';
import './Gerar.css';

export default function Gerar() {
  const [docxFile, setDocxFile] = useState(null);
  const [pptxFile, setPptxFile] = useState(null);
  const [nomeSaida, setNomeSaida] = useState('missa_pronta');
  const [validacao, setValidacao] = useState(null);
  const [validando, setValidando] = useState(false);
  const [secoesEditadas, setSecoesEditadas] = useState(null);
  const [log, setLog] = useState([]);
  const { call, loading, error, setError } = useApi();

  const handleDocxChange = async (e) => {
    const file = e.target.files[0];
    setDocxFile(file);
    setValidacao(null);
    setSecoesEditadas(null);
    setError(null);
    if (!file) return;

    setValidando(true);
    try {
      const resultado = await validarDocx(file);
      setValidacao(resultado);
      if (resultado.valido || resultado.secoes.length > 0) {
        setSecoesEditadas(resultado.secoes.map((s) => ({ titulo: s.titulo, linhas: s.linhas })));
      }
    } catch {
      setValidacao({ valido: false, erros: ['Não foi possível validar o arquivo.'], avisos: [], secoes: [] });
    } finally {
      setValidando(false);
    }
  };

  const handleGerar = async (e) => {
    e.preventDefault();
    setLog([]);
    setError(null);

    if (!docxFile) { setError('Selecione um arquivo .docx'); return; }
    if (!pptxFile) { setError('Selecione um arquivo .pptx'); return; }
    if (validacao && !validacao.valido) { setError('Corrija os erros no arquivo antes de gerar.'); return; }

    try {
      setLog(prev => [...prev, 'Enviando arquivos...']);
      let blob;
      if (secoesEditadas) {
        blob = await call(gerarEditado, secoesEditadas, pptxFile, nomeSaida);
      } else {
        blob = await call(gerarApresentacao, docxFile, pptxFile, nomeSaida);
      }
      setLog(prev => [...prev, '✓ Apresentação gerada com sucesso!']);
      const filename = nomeSaida.endsWith('.pptx') ? nomeSaida : nomeSaida + '.pptx';
      downloadFile(blob, filename);
    } catch (err) {
      setLog(prev => [...prev, '✗ Erro ao gerar: ' + (error || err.message)]);
    }
  };

  const temErros = validacao && validacao.erros.length > 0;
  const temAvisos = validacao && validacao.avisos.length > 0;

  return (
    <div className="gerar-container">
      <div className="gerar-header">
        <h2>Gerar Apresentação</h2>
        <p>Insira os arquivos e clique em Gerar</p>
      </div>

      <form onSubmit={handleGerar} className="gerar-form">
        <div className="form-group">
          <label>Cantos (.docx)</label>
          <input
            type="file"
            accept=".docx"
            onChange={handleDocxChange}
            disabled={loading}
          />
          <div className="dica-formato">
            Os títulos das seções devem estar em <strong>MAIÚSCULAS</strong> no documento.
            Ex: <code>ABERTURA</code>, <code>GLÓRIA</code>, <code>SANTO</code>, <code>COMUNHÃO</code>
          </div>
          {docxFile && <span className="file-name">{docxFile.name}</span>}
        </div>

        {validando && <div className="validacao-loading">Verificando arquivo...</div>}

        {validacao && (
          <div className={`validacao-panel ${temErros ? 'tem-erros' : temAvisos ? 'tem-avisos' : 'ok'}`}>
            <div className="validacao-titulo">
              {temErros ? '❌ Arquivo com problemas' : temAvisos ? '⚠️ Arquivo válido com avisos' : '✓ Arquivo válido'}
            </div>

            {validacao.erros.map((e, i) => (
              <div key={i} className="validacao-item erro">❌ {e}</div>
            ))}
            {validacao.avisos.map((a, i) => (
              <div key={i} className="validacao-item aviso">⚠️ {a}</div>
            ))}
          </div>
        )}

        {secoesEditadas && secoesEditadas.length > 0 && (
          <ListaCantos
            secoes={validacao.secoes}
            onChange={setSecoesEditadas}
          />
        )}

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
          <label>Nome do arquivo de saída</label>
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

        <button type="submit" disabled={loading || temErros} className="btn-primary">
          {loading ? 'Gerando...' : 'Gerar Apresentação'}
        </button>
      </form>

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
    </div>
  );
}
