import { useState, useEffect } from 'react';
import CantoEditor from './CantoEditor';
import './ListaCantos.css';

export default function ListaCantos({ secoes, onChange }) {
  const [secoesEditadas, setSecoesEditadas] = useState(() =>
    secoes.map((s) => ({ titulo: s.titulo, linhas: s.linhas }))
  );

  useEffect(() => {
    setSecoesEditadas(secoes.map((s) => ({ titulo: s.titulo, linhas: s.linhas })));
  }, [secoes]);

  const handleChange = (index, novasLinhas) => {
    const atualizadas = secoesEditadas.map((s, i) =>
      i === index ? { ...s, linhas: novasLinhas } : s
    );
    setSecoesEditadas(atualizadas);
    onChange(atualizadas);
  };

  return (
    <div className="lista-cantos">
      <div className="lista-cantos-header">
        <h3>Cantos interpretados</h3>
        <p>Revise o texto e o negrito de cada canto antes de gerar. Use linha em branco para separar slides.</p>
      </div>
      <div className="lista-cantos-cards">
        {secoesEditadas.map((s, i) => (
          <CantoEditor
            key={s.titulo + i}
            titulo={s.titulo}
            linhas={s.linhas}
            onChange={(novasLinhas) => handleChange(i, novasLinhas)}
          />
        ))}
      </div>
    </div>
  );
}
