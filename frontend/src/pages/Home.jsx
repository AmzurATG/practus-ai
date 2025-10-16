import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BarChart3, Database, CheckCircle, ArrowRight } from 'lucide-react'
import ConnectionModal from '../components/ConnectionModal'

export default function Home() {
  const [showConnectionModal, setShowConnectionModal] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const navigate = useNavigate()

  const handleConnectData = () => {
    setShowConnectionModal(true)
  }

  const handleConnectionSuccess = (connectionData) => {
    setIsConnected(true)
    // Redirect to insights page after successful connection
    setTimeout(() => {
      navigate('/insights')
    }, 1000)
  }

  return (
    <div className="space-y-10">
      <section className="text-center">
        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent">
          Practus AI — Actionable Intelligence
        </h1>
        <p className="mt-3 text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
          Connect your data, ask questions in plain English, and get prioritized actions across six core business problems.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <button 
            onClick={handleConnectData}
            className="px-5 py-3 rounded-md bg-blue-600 text-white hover:bg-blue-700 inline-flex items-center transition-colors"
          >
            <Database className="w-4 h-4 mr-2"/>
            {isConnected ? 'Data Connected' : 'Connect Data'}
            {isConnected && <CheckCircle className="w-4 h-4 ml-2" />}
          </button>
          <Link to="/visualization" className="px-5 py-3 rounded-md bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 inline-flex items-center">
            <BarChart3 className="w-4 h-4 mr-2"/>Explore
          </Link>
        </div>
      </section>

      {/* Connection Status */}
      {isConnected && (
        <section className="text-center">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 max-w-2xl mx-auto">
            <div className="flex items-center justify-center space-x-2 mb-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              <h2 className="text-lg font-semibold text-green-900">Data Successfully Connected</h2>
            </div>
            <p className="text-green-800 mb-4">
              Your data is ready for analysis. You can now explore insights and get actionable recommendations.
            </p>
            <Link 
              to="/insights" 
              className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              View Insights
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </div>
        </section>
      )}

      {/* Features Overview */}
      <section className="text-center">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">What You Can Do</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mx-auto mb-4">
              <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Revenue Forecasting</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Predict near-term revenues from your pipeline with AI-powered forecasting</p>
          </div>
          
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Database className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Deal Analysis</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Find and fix stage bottlenecks in your sales funnel</p>
          </div>
          
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Actionable Insights</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Get prioritized recommendations with clear next steps</p>
          </div>
        </div>
      </section>

      {/* Connection Modal */}
      <ConnectionModal
        isOpen={showConnectionModal}
        onClose={() => setShowConnectionModal(false)}
        onSuccess={handleConnectionSuccess}
      />
    </div>
  )
}


