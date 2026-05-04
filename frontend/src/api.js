import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

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
