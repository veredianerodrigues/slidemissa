import { useState } from 'react';
import { analisarDocx } from '../api';
import './Conversor.css';

const TITULOS_PADRAO = [
  'CANTO DE ENTRADA',
  'CANTO DO ATO PENITENCIAL',
  'CANTO DO GLÓRIA',
  'CANTO DE ACLAMAÇÃO',
  'CANTO DO OFERTÓRIO',
  'SANTO',
  'CANTO DE COMUNHÃO',
  'CANTO FINAL',
];

const CONFIDENCE_LABELS = {
  auto: 'Sequência',
  keyword: 'Palavra-chave',
  unknown: 'Revisar',
};

function ConfidenceBadge({ confidence }) {
  return (
    <span className={`confidence-badge confidence-${confidence}`}>
      {CONFIDENCE_LABELS[confidence] || confidence}
    </span>
  );
}

function buildTxt(sections) {
  const parts = [];
  for (const section of sections) {
    if (!section.title || section.title === '—') continue;
    parts.push(`[${section.title}]`);
    for (const line of section.lines) {
      const s = line.trim();
      if (s) parts.push(s);
    }
    parts.push('');
  }
  return parts.join('\n').trim();
}

function Conversor() {
  const [docxFile, setDocxFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [log, setLog] = useState([]);
  const [sections, setSections] = useState(null);
  const [modoAvancado, setModoAvancado] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && file.name.endsWith('.docx')) {
      setDocxFile(file);
      setError(null);
      setLog([]);
      setSections(null);
      setModoAvancado(false);
    } else {
      setError('Selecione um arquivo .docx válido');
      setDocxFile(null);
    }
  };

  const handleAnalisar = async () => {
    if (!docxFile) return;
    setLoading(true);
    setError(null);
    setLog(['Analisando DOCX...']);
    try {
      const data = await analisarDocx(docxFile);
      setSections(data.sections);
      const unknown = data.sections.filter(s => s.confidence === 'unknown').length;
      const msg = `✓ ${data.sections.length} seção(ões) detectada(s)${unknown ? ` — ${unknown} precisam revisão` : ''}`;
      setLog([msg]);
    } catch (err) {
      setError('Erro ao analisar: ' + (err.response?.data?.detail || err.message));
      setLog(['✗ Erro na análise']);
    } finally {
      setLoading(false);
    }
  };

  const handleTitleChange = (idx, newTitle) => {
    setSections(prev =>
      prev.map((s, i) => i === idx ? { ...s, title: newTitle, confidence: 'unknown' } : s)
    );
  };

  const handleConfirmar = () => {
    const txt = buildTxt(sections);
    const blob = new Blob([txt], { type: 'text/plain; charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = docxFile.name.replace('.docx', '.txt');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setLog(prev => [...prev, '✓ Arquivo baixado!']);
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

        {error && <div className="error-message">{error}</div>}

        <div className="log-section">
          <div className="log-box">
            {log.map((msg, i) => <div key={i} className="log-line">{msg}</div>)}
          </div>
        </div>

        <button
          className="btn-converter"
          onClick={handleAnalisar}
          disabled={!docxFile || loading}
        >
          {loading ? 'Analisando...' : 'Analisar DOCX'}
        </button>

        {sections && (
          <div className="mapping-section">
            <div className="mapping-header">
              <h3>Seções detectadas ({sections.length})</h3>
              <button
                className="btn-modo-avancado"
                onClick={() => setModoAvancado(v => !v)}
              >
                {modoAvancado ? '← Modo Simples' : 'Ajustar manualmente →'}
              </button>
            </div>

            <div className="mapping-table">
              {sections.map((section, idx) => (
                <div key={idx} className={`mapping-row confidence-row-${section.confidence}`}>
                  <span className="mapping-index">{idx + 1}</span>
                  <div className="mapping-title">
                    {modoAvancado ? (
                      <select
                        value={section.title}
                        onChange={(e) => handleTitleChange(idx, e.target.value)}
                        className="mapping-select"
                      >
                        {TITULOS_PADRAO.map(t => (
                          <option key={t} value={t}>{t}</option>
                        ))}
                        <option value="—">— ignorar —</option>
                      </select>
                    ) : (
                      <span className="mapping-title-text">{section.title}</span>
                    )}
                    <ConfidenceBadge confidence={section.confidence} />
                  </div>
                  <div className="mapping-preview">
                    {section.lines.slice(0, 1).map(l => l.replace(/^\* /, '')).join('').substring(0, 60)}
                    {section.lines.length > 1 ? ' ...' : ''}
                  </div>
                </div>
              ))}
            </div>

            <button
              className="btn-converter"
              onClick={handleConfirmar}
              disabled={loading}
            >
              Confirmar e Baixar TXT
            </button>
            <p className="preview-hint">
              ✓ Use este TXT na aba "Gerar via TXT"
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Conversor;
