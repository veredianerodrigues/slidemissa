import { useState } from 'react';
import Gerar from './components/Gerar';
import Login from './components/Login';
import './App.css';

function App() {
  const [autenticado, setAutenticado] = useState(
    () => sessionStorage.getItem('auth') === '1'
  );

  if (!autenticado) {
    return <Login onAutenticado={() => setAutenticado(true)} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Gerador de Slides da Missa</h1>
        <p>Gere apresentações para celebrações litúrgicas</p>
      </header>

      <main className="app-content">
        <Gerar />
      </main>

      <footer className="app-footer">
        <p>Slide Missa © 2026 — Verediane</p>
      </footer>
    </div>
  );
}

export default App;
