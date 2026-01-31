import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { documentsApi } from '../services/api';
import './DocumentList.css';

const DocumentList = ({ onUtilityResult }) => {
  const [uploading, setUploading] = useState(false);
  const [loadingAction, setLoadingAction] = useState(null); // e.g. "3-summarize"
  const queryClient = useQueryClient();

  // Fetch documents
  const { data: documents, isLoading } = useQuery(
    'documents',
    () => documentsApi.list().then(res => {
      if (res.data && Array.isArray(res.data.results)) {
        return res.data.results;
      }
      return Array.isArray(res.data) ? res.data : [];
    }),
    {
      refetchInterval: (data) => {
        if (!Array.isArray(data)) return false;
        const hasProcessing = data.some(doc => doc.status === 'PROCESSING');
        return hasProcessing ? 3000 : false;
      },
    }
  );

  // Upload mutation
  const uploadMutation = useMutation(
    (formData) => documentsApi.upload(formData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('documents');
        setUploading(false);
      },
      onError: (error) => {
        console.error('Upload error:', error);
        setUploading(false);
        alert('Upload failed. Please try again.');
      },
    }
  );

  const handleFileUpload = useCallback((event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name);

    setUploading(true);
    uploadMutation.mutate(formData);
  }, [uploadMutation]);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);

      setUploading(true);
      uploadMutation.mutate(formData);
    }
  };

  const handleUtilityAction = async (docId, action) => {
    const key = `${docId}-${action}`;
    setLoadingAction(key);
    try {
      const response = await documentsApi.utility(docId, action);
      if (onUtilityResult) {
        onUtilityResult(response.data);
      }
    } catch (error) {
      console.error('Utility action error:', error);
      const errorMsg = error.response?.data?.error || 'Action failed. Please try again.';
      alert(errorMsg);
    } finally {
      setLoadingAction(null);
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      'UPLOADED': 'status-uploaded',
      'PROCESSING': 'status-processing',
      'READY': 'status-ready',
      'FAILED': 'status-failed',
    };

    return (
      <span className={`status-badge ${statusClasses[status] || ''}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="document-list">
      <h2>Documents</h2>

      {/* Upload Area */}
      <div
        className="upload-area"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept=".pdf,.docx,.txt,.jpg,.jpeg,.png"
          onChange={handleFileUpload}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-upload" className="upload-label">
          {uploading ? (
            <>
              <span className="upload-icon">...</span>
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <span className="upload-icon">+</span>
              <span>Click or drag files here</span>
              <small>PDF, DOCX, TXT, JPG, PNG</small>
            </>
          )}
        </label>
      </div>

      {/* Document List */}
      <div className="documents-container">
        {isLoading ? (
          <div className="loading">Loading documents...</div>
        ) : documents && documents.length > 0 ? (
          <div className="document-items">
            {documents.map((doc) => (
              <div key={doc.id} className="document-item">
                <div className="document-icon">
                  {doc.file_type === 'pdf' && 'PDF'}
                  {doc.file_type === 'docx' && 'DOC'}
                  {doc.file_type === 'txt' && 'TXT'}
                  {['jpg', 'jpeg', 'png'].includes(doc.file_type) && 'IMG'}
                </div>
                <div className="document-info">
                  <div className="document-title">{doc.title}</div>
                  <div className="document-meta">
                    {getStatusBadge(doc.status)}
                    <span className="document-chunks">
                      {doc.num_chunks} chunks
                    </span>
                  </div>
                  <div className="document-date">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </div>
                  {doc.error_message && (
                    <div className="error-message">{doc.error_message}</div>
                  )}

                  {/* Utility action buttons — only for READY documents */}
                  {doc.status === 'READY' && (
                    <div className="utility-actions">
                      <button
                        className="utility-btn utility-btn-summarize"
                        onClick={() => handleUtilityAction(doc.id, 'summarize')}
                        disabled={loadingAction !== null}
                        title="Summarize this document"
                      >
                        {loadingAction === `${doc.id}-summarize` ? 'Processing...' : 'Summarize'}
                      </button>
                      <button
                        className="utility-btn utility-btn-translate"
                        onClick={() => handleUtilityAction(doc.id, 'translate')}
                        disabled={loadingAction !== null}
                        title="Translate this document"
                      >
                        {loadingAction === `${doc.id}-translate` ? 'Processing...' : 'Translate'}
                      </button>
                      <button
                        className="utility-btn utility-btn-checklist"
                        onClick={() => handleUtilityAction(doc.id, 'checklist')}
                        disabled={loadingAction !== null}
                        title="Generate checklist from document"
                      >
                        {loadingAction === `${doc.id}-checklist` ? 'Processing...' : 'Checklist'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-documents">
            <p>No documents uploaded yet</p>
            <p>Upload a document to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentList;
