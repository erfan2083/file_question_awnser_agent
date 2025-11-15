import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { documentsApi } from '../services/api';
import './DocumentList.css';

const DocumentList = () => {
  const [uploading, setUploading] = useState(false);
  const queryClient = useQueryClient();
  
  // Fetch documents
  const { data: documents, isLoading, refetch } = useQuery(
    'documents',
    () => documentsApi.list().then(res => res.data),
    {
      refetchInterval: (data) => {
        // Poll every 3 seconds if any document is processing
        const hasProcessing = data?.some(doc => doc.status === 'PROCESSING');
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
      <h2>📄 Documents</h2>
      
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
              <span className="upload-icon">⏳</span>
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <span className="upload-icon">📤</span>
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
                  {doc.file_type === 'pdf' && '📕'}
                  {doc.file_type === 'docx' && '📘'}
                  {doc.file_type === 'txt' && '📄'}
                  {['jpg', 'jpeg', 'png'].includes(doc.file_type) && '🖼️'}
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
