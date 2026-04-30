import { useState } from 'react';
import { gerarApresentacao } from '../api';
import { useApi, downloadFile } from '../hooks/useApi';
import './Gerar.css';

export default function Gerar() {
  const [txtFile, setTxtFile] = useState(null);
  const [pptxFile, setPptxFile] = useState(null);
  const [nomeSaida, setNomeSaida] = useState('missa_pronta');
  const [log, setLog] = useState([]);
  const { call, loading, error, setError } = useApi();

  const handleGerar = async (e) => {
    e.preventDefault();
    setLog([]);
    setError(null);

    if (!txtFile) {
      setError('Selecione um arquivo .txt');
      return;
    }
    if (!pptxFile) {
      setError('Selecione um arquivo .pptx');
      return;
    }

    try {
      setLog(prev => [...prev, 'Enviando arquivos...']);
      const blob = await call(gerarApresentacao, txtFile, pptxFile, nomeSaida);
      setLog(prev => [...prev, '✓ Apresentação gerada com sucesso!']);
      
      const filename = nomeSaida.endsWith('.pptx') ? nomeSaida : nomeSaida + '.pptx';
      downloadFile(blob, filename);
    } catch (err) {
      setLog(prev => [...prev, '✗ Erro ao gerar: ' + (error || err.message)]);
    }
  };

  return (
    <div className="gerar-container">
      <div className="gerar-header">
        <h2>Gerar via TXT</h2>
        <p>Insira os arquivos e clique em Gerar</p>
      </div>

      <form onSubmit={handleGerar} className="gerar-form">
        <div className="form-group">
          <label>Cantos (.txt)</label>
          <input
            type="file"
            accept=".txt"
            onChange={(e) => setTxtFile(e.target.files[0])}
            disabled={loading}
          />
          {txtFile && <span className="file-name">{txtFile.name}</span>}
        </div>

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

        <button type="submit" disabled={loading} className="btn-primary">
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
