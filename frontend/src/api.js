import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const gerarApresentacao = async (txtFile, pptxFile, nomeSaida) => {
  const formData = new FormData();
  formData.append('txt', txtFile);
  formData.append('pptx', pptxFile);
  formData.append('nome_saida', nomeSaida);

  const response = await axios.post(`${API_BASE}/gerar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob'
  });

  return response.data;
};

export const obterPosicoes = async () => {
  const response = await axios.get(`${API_BASE}/banco/posicoes`);
  return response.data.posicoes;
};

export const listarCantos = async (posicao = null) => {
  const params = posicao && posicao !== 'Todas' ? { posicao } : {};
  const response = await axios.get(`${API_BASE}/banco/listar`, { params });
  return response.data.cantos;
};

export const gerarDoBanco = async (pptxFile, chaves, nomeSaida) => {
  const formData = new FormData();
  formData.append('pptx', pptxFile);
  chaves.forEach((chave) => {
    formData.append('chaves', chave);
  });
  formData.append('nome_saida', nomeSaida);

  const response = await axios.post(`${API_BASE}/gerar-do-banco`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob'
  });

  return response.data;
};

export const deletarCanto = async (cantoId) => {
  await axios.delete(`${API_BASE}/banco/${cantoId}`);
};

export const deletarVarios = async (ids) => {
  const response = await axios.post(`${API_BASE}/banco/deletar-varios`, { ids });
  return response.data;
};

export const analisarDocx = async (docxFile) => {
  const formData = new FormData();
  formData.append('docx', docxFile);

  const response = await axios.post(`${API_BASE}/analisar-docx`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });

  return response.data;
};

export const obterTitulosPadrao = async () => {
  const response = await axios.get(`${API_BASE}/titulos-padrao`);
  return response.data.titulos;
};

export const montarTxt = async (sections) => {
  const response = await axios.post(`${API_BASE}/montar-txt`, { sections });
  return response.data.txt;
};

export const gerarPptxCantos = async (chaves, nomeSaida) => {
  const response = await axios.post(`${API_BASE}/gerar-pptx-cantos`, {
    chaves,
    nome_saida: nomeSaida
  }, {
    responseType: 'blob'
  });

  return response.data;
};
