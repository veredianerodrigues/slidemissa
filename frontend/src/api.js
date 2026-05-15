import axios from 'axios';

const API_BASE = '/api';

export const validarDocx = async (docxFile) => {
  const formData = new FormData();
  formData.append('docx', docxFile);
  const response = await axios.post(`${API_BASE}/validar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const gerarApresentacao = async (docxFile, pptxFile, nomeSaida) => {
  const formData = new FormData();
  formData.append('docx', docxFile);
  formData.append('pptx', pptxFile);
  formData.append('nome_saida', nomeSaida);

  const response = await axios.post(`${API_BASE}/gerar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob'
  });

  return response.data;
};
