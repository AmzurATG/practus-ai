import { useState, useEffect } from 'react'
import { X, CheckCircle, AlertCircle, Database, Loader2 } from 'lucide-react'
import axios from 'axios'

const ConnectionModal = ({ isOpen, onClose, onSuccess }) => {
  const [connectionStatus, setConnectionStatus] = useState('connecting') // connecting, success, error
  const [currentFile, setCurrentFile] = useState(0)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)
  const [connectionData, setConnectionData] = useState(null)

  const files = [
    { name: 'Deals Archive.csv', size: '1.5MB', rows: '3,970' },
    { name: 'Stage History Archive.csv', size: '981KB', rows: '6,643' },
    { name: 'Whizible data.csv', size: '6.0MB', rows: '57,260' },
    { name: 'Plotting tool data.csv', size: '53KB', rows: '585' },
    { name: 'Skill mapping.csv', size: '4.5MB', rows: '45,000' },
    { name: 'Metrics.csv', size: '955B', rows: '18' }
  ]

  useEffect(() => {
    if (isOpen) {
      startConnection()
    }
  }, [isOpen])

  const startConnection = async () => {
    setConnectionStatus('connecting')
    setCurrentFile(0)
    setProgress(0)
    setError(null)

    try {
      // Simulate file loading progress
      for (let i = 0; i < files.length; i++) {
        setCurrentFile(i)
        setProgress((i / files.length) * 80) // 80% for file loading
        
        // Simulate file processing time
        await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 500))
      }

      // Make actual connection request
      setProgress(85)
      const token = localStorage.getItem('token')
      const response = await axios.post('http://localhost:8080/api/datasource/connect', {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      setProgress(100)
      setConnectionData(response.data)
      setConnectionStatus('success')

      // Auto-close after success
      setTimeout(() => {
        onSuccess(response.data)
        onClose()
      }, 2000)

    } catch (err) {
      console.error('Connection error:', err)
      setError(err.response?.data?.detail || 'Connection failed')
      setConnectionStatus('error')
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connecting':
        return <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      case 'success':
        return <CheckCircle className="w-8 h-8 text-green-500" />
      case 'error':
        return <AlertCircle className="w-8 h-8 text-red-500" />
      default:
        return <Database className="w-8 h-8 text-gray-500" />
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'Connecting to Supabase...'
      case 'success':
        return 'Connection Successful!'
      case 'error':
        return 'Connection Failed'
      default:
        return 'Ready to Connect'
    }
  }

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'text-blue-600'
      case 'success':
        return 'text-green-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Connect Data Source</h2>
              <p className="text-sm text-gray-500">Establishing connection to Supabase</p>
            </div>
          </div>
          {connectionStatus !== 'connecting' && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Connection Status */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              {getStatusIcon()}
            </div>
            <h3 className={`text-lg font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </h3>
            {connectionStatus === 'connecting' && (
              <p className="text-sm text-gray-600 mt-2">
                Loading data files and validating connection...
              </p>
            )}
          </div>

          {/* Progress Bar */}
          {connectionStatus === 'connecting' && (
            <div className="mb-8">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* File Loading List */}
          <div className="space-y-3 mb-6">
            <h4 className="font-medium text-gray-900">Data Files</h4>
            {files.map((file, index) => {
              const isLoaded = index < currentFile
              const isCurrent = index === currentFile && connectionStatus === 'connecting'
              const isCompleted = connectionStatus === 'success'

              return (
                <div 
                  key={file.name}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-200 ${
                    isCompleted ? 'bg-green-50 border-green-200' :
                    isLoaded ? 'bg-blue-50 border-blue-200' :
                    isCurrent ? 'bg-yellow-50 border-yellow-200' :
                    'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      isCompleted ? 'bg-green-500' :
                      isLoaded ? 'bg-blue-500' :
                      isCurrent ? 'bg-yellow-500' :
                      'bg-gray-300'
                    }`}>
                      {isCompleted ? (
                        <CheckCircle className="w-4 h-4 text-white" />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 text-white animate-spin" />
                      ) : isLoaded ? (
                        <CheckCircle className="w-4 h-4 text-white" />
                      ) : (
                        <div className="w-2 h-2 bg-white rounded-full" />
                      )}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900">{file.name}</div>
                      <div className="text-sm text-gray-500">
                        {file.size} • {file.rows} rows
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {isCompleted ? 'Loaded' :
                     isLoaded ? 'Complete' :
                     isCurrent ? 'Loading...' :
                     'Pending'}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Supabase Connection Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-2 mb-2">
              <Database className="w-5 h-5 text-blue-600" />
              <h4 className="font-medium text-blue-900">Supabase Connection</h4>
            </div>
            <div className="text-sm text-blue-800">
              <div>URL: https://liqretxkmjvwbfvvvzuy.supabase.co</div>
              <div>Tables: 6 tables synchronized</div>
              <div>Status: {connectionStatus === 'success' ? 'Connected' : 'Connecting...'}</div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <h4 className="font-medium text-red-900">Connection Error</h4>
              </div>
              <p className="text-sm text-red-800 mt-1">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {connectionStatus === 'success' && connectionData && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <h4 className="font-medium text-green-900">Connection Successful</h4>
              </div>
              <div className="text-sm text-green-800 space-y-1">
                <div>Files loaded: {connectionData.files_loaded}</div>
                <div>Total rows: {connectionData.total_rows?.toLocaleString()}</div>
                <div>Data source: Local files synchronized with Supabase</div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3">
            {connectionStatus === 'error' && (
              <button
                onClick={startConnection}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Retry Connection
              </button>
            )}
            {connectionStatus === 'success' && (
              <button
                onClick={() => {
                  onSuccess(connectionData)
                  onClose()
                }}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                Continue
              </button>
            )}
            {connectionStatus !== 'connecting' && (
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConnectionModal
