import React, { useState, useEffect } from 'react';
import { documentsAPI } from '../services/api';
import './DocumentList.css';

const DocumentList = ({ onDocumentClick }) => {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await documentsAPI.list();
      setDocuments(response.data.results || []);
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      await documentsAPI.upload(file);
      await fetchDocuments();
    } catch (err) {
      setError('Failed to upload document. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      UPLOADED: 'status-uploaded',
      PROCESSING: 'status-processing',
      READY: 'status-ready',
      FAILED: 'status-failed',
    };
    return (
      <span className={`status-badge ${statusClasses[status] || ''}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="document-list">
      <div className="upload-section">
        <h3>Upload Document</h3>
        <label htmlFor="file-upload" className="upload-button">
          {uploading ? 'Uploading...' : 'Choose File'}
        </label>
        <input
          id="file-upload"
          type="file"
          accept=".pdf,.docx,.txt,.jpg,.jpeg,.png"
          onChange={handleFileUpload}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        <p className="upload-hint">
          Supported: PDF, DOCX, TXT, JPG, PNG
        </p>
        {error && <div className="error-message">{error}</div>}
      </div>

      <div className="documents-section">
        <h3>Documents ({documents.length})</h3>
        <div className="documents-container">
          {documents.length === 0 ? (
            <p className="no-documents">No documents uploaded yet</p>
          ) : (
            documents.map((doc) => (
              <div
                key={doc.id}
                className="document-item"
                onClick={() => onDocumentClick && onDocumentClick(doc)}
              >
                <div className="document-header">
                  <span className="document-title">{doc.title}</span>
                  {getStatusBadge(doc.status)}
                </div>
                <div className="document-meta">
                  <span className="document-type">{doc.file_type}</span>
                  <span className="document-chunks">
                    {doc.chunks_count} chunks
                  </span>
                  <span className="document-date">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                </div>
                {doc.error_message && (
                  <div className="document-error">{doc.error_message}</div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentList;
