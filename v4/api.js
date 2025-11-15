import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Documents API
export const documentsAPI = {
  list: () => api.get('/documents/'),
  get: (id) => api.get(`/documents/${id}/`),
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getChunks: (id) => api.get(`/documents/${id}/chunks/`),
};

// Chat API
export const chatAPI = {
  listSessions: () => api.get('/chat/sessions/'),
  createSession: () => api.post('/chat/sessions/', {}),
  getSession: (id) => api.get(`/chat/sessions/${id}/`),
  getMessages: (sessionId) => api.get(`/chat/sessions/${sessionId}/messages/`),
  sendMessage: (sessionId, content) =>
    api.post(`/chat/sessions/${sessionId}/messages/`, { content }),
};

// Evaluation API
export const evaluationAPI = {
  listResults: () => api.get('/evaluation/results/'),
  runEvaluation: () => api.post('/evaluation/results/run/'),
  listQueries: () => api.get('/evaluation/queries/'),
};

export default api;
