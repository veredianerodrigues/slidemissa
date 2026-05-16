import { useState } from 'react';
import './Login.css';

const SENHA = 'missa2026';

export default function Login({ onAutenticado }) {
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (senha === SENHA) {
      sessionStorage.setItem('auth', '1');
      onAutenticado();
    } else {
      setErro(true);
      setSenha('');
    }
  };

  return (
    <div className="login-overlay">
      <div className="login-box">
        <div className="login-logo">
          <h1>Slide Missa</h1>
          <p>Gerador de apresentações litúrgicas</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="senha">Senha de acesso</label>
          <input
            id="senha"
            type="password"
            value={senha}
            onChange={(e) => { setSenha(e.target.value); setErro(false); }}
            placeholder="Digite a senha"
            autoFocus
          />
          {erro && <div className="login-erro">Senha incorreta.</div>}
          <button type="submit">Entrar</button>
        </form>
      </div>
    </div>
  );
}
