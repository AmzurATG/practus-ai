import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Plot from 'react-plotly.js'
import axios from 'axios'
import { TrendingUp, TrendingDown, AlertCircle, BarChart3, Target, Users, Briefcase, Zap, Settings } from 'lucide-react'

const problems = [
  { id: 1, title: 'Revenue Forecasting', icon: TrendingUp, color: 'blue' },
  { id: 2, title: 'Deal Drop-off Analysis', icon: Target, color: 'red' },
  { id: 3, title: 'Effort vs Budget Tracking', icon: BarChart3, color: 'green' },
  { id: 4, title: 'Client Retention Insights', icon: Users, color: 'purple' },
  { id: 5, title: 'Data-Driven Hiring Decisions', icon: Briefcase, color: 'orange' },
  { id: 6, title: 'Delivery Operations Automation', icon: Zap, color: 'indigo' },
]

export default function Visualization() {
  const [selectedProblem, setSelectedProblem] = useState(1)
  const [problemData, setProblemData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadProblemData(selectedProblem)
  }, [selectedProblem])

  const loadProblemData = async (problemId) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }

      const response = await axios.get(`/api/visualizations/problem/${problemId}`, { headers })
      setProblemData(response.data)
    } catch (err) {
      console.error('Failed to load problem data', err)
      setProblemData({ error: 'Failed to load data' })
    } finally {
      setLoading(false)
    }
  }

  const renderChart = (viz) => {
    if (!viz.data || (!viz.data.x && !viz.data.labels)) {
      return <div className="text-center py-8 text-gray-500">No data available for this visualization</div>
    }

    const colorMap = {
      blue: '#3b82f6',
      red: '#ef4444', 
      green: '#10b981',
      purple: '#8b5cf6',
      orange: '#f59e0b',
      indigo: '#6366f1'
    }

    const currentProblem = problems.find(p => p.id === selectedProblem)
    const color = colorMap[currentProblem?.color] || '#3b82f6'

    if (viz.type === 'line') {
      // Check if this is a forecast chart
      const isForecast = viz.data.forecast_start_index !== undefined
      const historicalData = isForecast ? {
        type: 'scatter',
        mode: 'lines+markers',
        x: viz.data.x.slice(0, viz.data.forecast_start_index),
        y: viz.data.y.slice(0, viz.data.forecast_start_index),
        line: { color: color, width: 3 },
        marker: { color: color, size: 8 },
        name: 'Actual'
      } : {
        type: 'scatter',
        mode: 'lines+markers',
        x: viz.data.x,
        y: viz.data.y,
        line: { color: color, width: 3 },
        marker: { color: color, size: 8 },
        text: viz.data.labels || viz.data.y.map(v => v.toFixed(0)),
        hovertemplate: '%{text}<extra></extra>'
      }

      const forecastData = isForecast ? {
        type: 'scatter',
        mode: 'lines+markers',
        x: viz.data.x.slice(viz.data.forecast_start_index - 1),
        y: viz.data.y.slice(viz.data.forecast_start_index - 1),
        line: { color: '#f59e0b', width: 3, dash: 'dash' },
        marker: { color: '#f59e0b', size: 8 },
        name: 'Forecast'
      } : null

      return (
        <Plot
          data={isForecast ? [historicalData, forecastData] : [historicalData]}
          layout={{
            height: 400,
            xaxis: { title: '', tickangle: -45 },
            yaxis: { title: '' },
            font: { family: 'Inter, sans-serif', size: 11 },
            margin: { t: 20, b: 80, l: 70, r: 20 },
            showlegend: isForecast,
            legend: { x: 0, y: 1.1, orientation: 'h' }
          }}
          config={{ responsive: true, displayModeBar: false }}
          className="w-full"
        />
      )
    } else if (viz.type === 'bar') {
      return (
        <Plot
          data={[{
            type: 'bar',
            x: viz.data.x,
            y: viz.data.y,
            marker: { color: color },
            text: viz.data.labels || viz.data.y.map(v => typeof v === 'number' ? v.toFixed(0) : v),
            textposition: 'outside',
            hovertemplate: '%{x}<br>%{text}<extra></extra>'
          }]}
          layout={{
            height: 400,
            xaxis: { tickangle: -45, automargin: true },
            yaxis: { automargin: true },
            font: { family: 'Inter, sans-serif', size: 11 },
            margin: { t: 30, b: 100, l: 80, r: 20 }
          }}
          config={{ responsive: true, displayModeBar: false }}
          className="w-full"
        />
      )
    } else if (viz.type === 'pie') {
      return (
        <Plot
          data={[{
            type: 'pie',
            labels: viz.data.labels,
            values: viz.data.values,
            textinfo: 'label+percent',
            textposition: 'auto',
            marker: { 
              colors: viz.data.labels.map((_, i) => {
                const alpha = Math.max(0.5, 1 - (i * 0.1))
                return `${color}${Math.floor(alpha * 255).toString(16).padStart(2, '0')}`
              })
            },
            hovertemplate: '%{label}<br>%{value}<br>%{percent}<extra></extra>'
          }]}
          layout={{
            height: 400,
            font: { family: 'Inter, sans-serif', size: 11 },
            margin: { t: 20, b: 20, l: 20, r: 20 },
            showlegend: true,
            legend: { orientation: 'v', x: 1, y: 0.5 }
          }}
          config={{ responsive: true, displayModeBar: false }}
          className="w-full"
        />
      )
    } else if (viz.type === 'funnel') {
      return (
        <Plot
          data={[{
            type: 'funnel',
            y: viz.data.stages,
            x: viz.data.counts,
            marker: { color: color },
            textposition: "inside",
            textinfo: "value+percent initial",
            hovertemplate: '%{y}<br>%{x} deals<br>%{percentInitial}<extra></extra>'
          }]}
          layout={{
            height: 500,
            margin: { l: 250, r: 50, t: 20, b: 50 },
            font: { family: 'Inter, sans-serif', size: 12 }
          }}
          config={{ responsive: true, displayModeBar: false }}
          className="w-full"
        />
      )
    } else if (viz.type === 'scatter') {
      return (
        <Plot
          data={[{
            type: 'scatter',
            mode: 'markers',
            x: viz.data.x,
            y: viz.data.y,
            marker: { color: color, size: 10 }
          }]}
          layout={{
            height: 400,
            xaxis: { title: '', automargin: true },
            yaxis: { title: '', automargin: true },
            font: { family: 'Inter, sans-serif', size: 11 },
            margin: { t: 20, b: 60, l: 60, r: 20 }
          }}
          config={{ responsive: true, displayModeBar: false }}
          className="w-full"
        />
      )
    } else if (viz.type === 'histogram') {
      return (
        <Plot
          data={[{
            type: 'histogram',
            x: viz.data.x,
            nbinsx: viz.data.bins || 20,
            marker: { color: color }
          }]}
          layout={{
            height: 400,
            xaxis: { title: '', automargin: true },
            yaxis: { title: 'Frequency', automargin: true },
            font: { family: 'Inter, sans-serif', size: 11 },
            margin: { t: 20, b: 60, l: 60, r: 20 }
          }}
          config={{ responsive: true, displayModeBar: false }}
          className="w-full"
        />
      )
    }
    
    return <div className="text-center py-8 text-gray-500">Unsupported chart type: {viz.type}</div>
  }

  if (loading) {
    return <div className="text-center py-12">Loading visualizations...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Data Visualization</h1>
          <p className="mt-2 text-gray-600">Problem-specific analysis and insights</p>
        </div>
        <button
          onClick={() => navigate('/devmode')}
          className="px-6 py-2 bg-gradient-to-r from-blue-600 to-green-600 text-white rounded-md hover:from-blue-700 hover:to-green-700"
        >
          Continue to Dev Mode →
        </button>
      </div>

      {/* Problem Selection Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {problems.map((problem) => {
              const Icon = problem.icon
              const isActive = selectedProblem === problem.id
              return (
                <button
                  key={problem.id}
                  onClick={() => setSelectedProblem(problem.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    isActive
                      ? `border-${problem.color}-500 text-${problem.color}-600`
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{problem.title}</span>
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* AI Insights */}
      {problemData?.insights && problemData.insights.length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 flex items-center">
            <span className="mr-2">🤖</span> AI-Generated Insights
          </h3>
          <div className="space-y-3">
            {problemData.insights.map((insight, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                <p className="text-gray-800">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Metrics */}
      {problemData?.summary && !problemData.error && (
        <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Key Metrics Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(problemData.summary).map(([key, value]) => (
              <div key={key} className="bg-white rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500 capitalize">
                  {key.replace(/_/g, ' ')}
                </div>
                <div className="text-2xl font-bold text-gray-900 mt-1">
                  {typeof value === 'number' 
                    ? value > 1000000 
                      ? `$${(value/1000000).toFixed(1)}M`
                      : value > 1000
                      ? value.toLocaleString()
                      : value.toFixed(0)
                    : value
                  }
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Problem-specific Visualizations */}
      {problemData?.error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{problemData.error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {problemData?.visualizations?.map((viz, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">{viz.title}</h3>
              {renderChart(viz)}
            </div>
          ))}
        </div>
      )}

      {/* Problem Description */}
      {problemData && !problemData.error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800 font-medium">
            ✓ {problemData.problem} analysis complete. {problemData.visualizations?.length || 0} visualizations generated with real-time data.
          </p>
        </div>
      )}
    </div>
  )
}

