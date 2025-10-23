import React, { useState } from 'react'
import axios from 'axios'
import { FaUpload, FaSpinner, FaCheckCircle, FaTimesCircle } from 'react-icons/fa'
import './FileUpload.css' // We'll create this file

const FileUpload = ({ onUploadStart, onUploadSuccess }) => {
  const [selectedFiles, setSelectedFiles] = useState(null)
  const [status, setStatus] = useState('idle') // idle, uploading, success, error
  const [message, setMessage] = useState('')

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setSelectedFiles(e.target.files)
      setStatus('idle')
      setMessage('')
    }
  }

  const handleUpload = async () => {
    if (!selectedFiles) return

    onUploadStart()
    setStatus('uploading')
    setMessage('Processing files...')

    const formData = new FormData()
    Array.from(selectedFiles).forEach(file => {
      formData.append('files', file)
    })

    try {
      // Use the proxied API path
      const response = await axios.post('/api/v1/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setStatus('success')
      setMessage(response.data.message || 'Files processed successfully!')
      onUploadSuccess()
    } catch (err) {
      console.error(err)
      setStatus('error')
      setMessage(err.response?.data?.detail || 'An error occurred during upload.')
    }
  }

  return (
    <div className="file-upload-container">
      <input
        type="file"
        id="file-input"
        className="file-input-hidden"
        multiple
        onChange={handleFileChange}
        accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
      />
      <label htmlFor="file-input" className="file-input-label">
        {selectedFiles ? `${selectedFiles.length} file(s) selected` : 'Choose files...'}
      </label>
      
      <button 
        onClick={handleUpload} 
        disabled={!selectedFiles || status === 'uploading'}
        className="upload-button"
      >
        {status === 'uploading' ? (
          <FaSpinner className="icon-spin" />
        ) : (
          <FaUpload />
        )}
        Upload
      </button>

      {message && (
        <div className={`status-message ${status}`}>
          {status === 'success' && <FaCheckCircle />}
          {status === 'error' && <FaTimesCircle />}
          {status === 'uploading' && <FaSpinner className="icon-spin" />}
          <p>{message}</p>
        </div>
      )}
    </div>
  )
}


export default FileUpload