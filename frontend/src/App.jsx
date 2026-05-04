import Gerar from './components/Gerar';
import './App.css';

function App() {
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
