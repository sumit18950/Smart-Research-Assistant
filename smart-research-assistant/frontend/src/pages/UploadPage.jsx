import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadDocument } from '../services/api'
import { useApi } from '../hooks/useApi'

export default function UploadPage() {
  const [uploads, setUploads] = useState([])
  const { loading, error, execute } = useApi(uploadDocument)

  const onDrop = useCallback(async (acceptedFiles) => {
    for (const file of acceptedFiles) {
      try {
        const result = await execute(file)
        setUploads(prev => [...prev, {
          filename: result.filename,
          chunks: result.total_chunks,
          docId: result.document_id,
          status: 'success',
        }])
      } catch {
        setUploads(prev => [...prev, {
          filename: file.name,
          chunks: 0,
          status: 'error',
        }])
      }
    }
  }, [execute])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  })

  return (
    <div>
      <div className="card">
        <h2 className="card-title">Upload Documents</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 16 }}>
          Upload PDF documents to build your research knowledge base.
          Documents are automatically extracted, chunked, and indexed for retrieval.
        </p>

        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          {loading ? (
            <p>Processing document<span className="loading-dots"></span></p>
          ) : isDragActive ? (
            <p>Drop your PDF files here</p>
          ) : (
            <p>
              Drag & drop PDF files here, or <span className="highlight">click to browse</span>
            </p>
          )}
          <p style={{ marginTop: 8, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            PDF files up to 50MB supported
          </p>
        </div>

        {error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: 12 }}>
            Error: {error}
          </div>
        )}
      </div>

      {uploads.length > 0 && (
        <div className="card">
          <h2 className="card-title">Processed Documents</h2>
          <div className="upload-list">
            {uploads.map((item, idx) => (
              <div key={idx} className="upload-item">
                <div>
                  <div className="filename">{item.filename}</div>
                  <div className="chunk-count">
                    {item.status === 'success'
                      ? `${item.chunks} chunks indexed | ID: ${item.docId}`
                      : 'Failed to process'}
                  </div>
                </div>
                <span className="status-icon" style={{ color: item.status === 'success' ? 'var(--success)' : 'var(--danger)' }}>
                  {item.status === 'success' ? '\u2713' : '\u2717'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
