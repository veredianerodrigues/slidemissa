import { useState } from 'react';
import { converterDocx } from '../api';
import './Conversor.css';

function Conversor() {
  const [docxFile, setDocxFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [log, setLog] = useState([]);
  const [preview, setPreview] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.name.endsWith('.docx')) {
      setDocxFile(file);
      setError(null);
      setLog([]);
      setPreview(null);
    } else {
      setError('Selecione um arquivo .docx válido');
      setDocxFile(null);
    }
  };

  const handleConverter = async () => {
    if (!docxFile) {
      setError('Selecione um arquivo DOCX');
      return;
    }

    setLoading(true);
    setError(null);
    setLog(['Convertendo DOCX para TXT...']);

    try {
      const txtContent = await converterDocx(docxFile);
      setLog(['✓ Conversão concluída!']);
      setPreview(txtContent);

      const blob = new Blob([txtContent], { type: 'text/plain; charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = docxFile.name.replace('.docx', '.txt');
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setLog(prev => [...prev, '✓ Arquivo baixado!']);
    } catch (err) {
      setError('Erro ao converter: ' + err.message);
      setLog(['✗ Erro na conversão']);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="conversor-container">
      <div className="conversor-card">
        <h2>Converter DOCX para TXT</h2>
        <p className="subtitle">Converta seu documento Word para o formato esperado</p>

        <div className="upload-section">
          <label className="file-input-label">
            <input
              type="file"
              accept=".docx"
              onChange={handleFileChange}
              disabled={loading}
            />
            <span className="file-input-text">
              {docxFile ? `✓ ${docxFile.name}` : 'Selecione arquivo DOCX'}
            </span>
          </label>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="log-section">
          <div className="log-box">
            {log.map((msg, i) => (
              <div key={i} className="log-line">{msg}</div>
            ))}
          </div>
        </div>

        <button
          className="btn-converter"
          onClick={handleConverter}
          disabled={!docxFile || loading}
        >
          {loading ? 'Convertendo...' : 'Converter e Baixar'}
        </button>

        {preview && (
          <div className="preview-section">
            <h3>Prévia do TXT Convertido</h3>
            <p className="preview-info">
              Revise o conteúdo antes de usar. Os títulos estão em [colchetes] e o negrito começa com *.
            </p>
            <textarea
              className="preview-box"
              readOnly
              value={preview}
            />
            <p className="preview-hint">
              ✓ Agora você pode fazer upload deste TXT na aba "Gerar via TXT"
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Conversor;
