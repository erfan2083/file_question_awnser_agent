import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Documents API
export const documentsApi = {
  upload: (formData) => {
    return api.post('/api/documents/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  list: () => api.get('/api/documents/'),
  
  get: (id) => api.get(`/api/documents/${id}/`),
  
  delete: (id) => api.delete(`/api/documents/${id}/`),
};

// Chat API
export const chatApi = {
  createSession: (data) => api.post('/api/chat/sessions/', data),
  
  listSessions: () => api.get('/api/chat/sessions/'),
  
  getMessages: (sessionId) => api.get(`/api/chat/sessions/${sessionId}/messages/`),
  
  sendMessage: (sessionId, content) => 
    api.post(`/api/chat/sessions/${sessionId}/messages/`, { content }),
  
  clearMessages: (sessionId) => 
    api.delete(`/api/chat/sessions/${sessionId}/clear/`),
};

// Evaluation API
export const evaluationApi = {
  runEvaluation: (data) => api.post('/api/evaluation/runs/run/', data),
  
  listRuns: () => api.get('/api/evaluation/runs/'),
  
  getRun: (id) => api.get(`/api/evaluation/runs/${id}/`),
};

export default api;
