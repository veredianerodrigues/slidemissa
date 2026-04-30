import { useState } from 'react';
import Gerar from './components/Gerar';
import Banco from './components/Banco';
import Conversor from './components/Conversor';
import './App.css';

function App() {
  const [aba, setAba] = useState('gerar');

  return (
    <div className="app">
      <header className="app-header">
        <h1>Gerador de Slides da Missa</h1>
        <p>Gere apresentações para celebrações litúrgicas</p>
      </header>

      <nav className="tabs">
        <button
          className={`tab ${aba === 'conversor' ? 'active' : ''}`}
          onClick={() => setAba('conversor')}
        >
          Converter DOCX
        </button>
        <button
          className={`tab ${aba === 'gerar' ? 'active' : ''}`}
          onClick={() => setAba('gerar')}
        >
          Gerar via TXT
        </button>
        <button
          className={`tab ${aba === 'banco' ? 'active' : ''}`}
          onClick={() => setAba('banco')}
        >
          Banco de Cantos
        </button>
      </nav>

      <main className="app-content">
        {aba === 'conversor' && <Conversor />}
        {aba === 'gerar' && <Gerar />}
        {aba === 'banco' && <Banco />}
      </main>

      <footer className="app-footer">
        <p>Slide Missa © 2024 — Versão Web</p>
      </footer>
    </div>
  );
}

export default App;
