import { useState, useEffect } from 'react'
import { TrendingUp, Target, BarChart3, Users, Briefcase, Zap, CheckCircle, Clock, AlertTriangle, AlertCircle, TrendingDown, DollarSign, Activity, Loader2, Cpu, Layers, Star, PieChart, ChevronDown, ChevronUp, Mail } from 'lucide-react'
import toast from 'react-hot-toast'

// AI Insights Formatting Component
const formatAIInsights = (insights) => {
  if (!insights) return null
  
  return (
    <div className="space-y-4">
      {insights.map((insight, index) => {
        if (insight === "") return <div key={index} className="h-2"></div>
        
        // Critical alerts (Critical alerts)
        if (insight.includes("Critical") || insight.includes("Alert")) {
          return (
            <div key={index} className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
              <p className="text-red-800 font-medium">{insight}</p>
            </div>
          )
        }
        
        // Section headers (text ending with colon)
        if (insight.endsWith(":") && !insight.includes("•") && !insight.match(/^\d+\./)) {
          return (
            <h4 key={index} className="font-bold text-gray-900 text-base mt-4 mb-2">
              {insight}
            </h4>
          )
        }
        
        // Bullet points (remove • and format as clean list)
        if (insight.startsWith("•")) {
          return (
            <div key={index} className="flex items-start ml-4">
              <span className="text-blue-500 mr-2 mt-1">•</span>
              <p className="text-gray-700">{insight.substring(1).trim()}</p>
            </div>
          )
        }
        
        // Numbered actions (1., 2., 3.)
        if (insight.match(/^\d+\./)) {
          return (
            <div key={index} className="flex items-start ml-4">
              <span className="text-green-600 mr-2 font-semibold">{insight.split('.')[0]}.</span>
              <p className="text-gray-700">{insight.substring(insight.indexOf('.') + 1).trim()}</p>
            </div>
          )
        }
        
        // Regular text
        return (
          <p key={index} className="text-gray-700 leading-relaxed">
            {insight}
          </p>
        )
      })}
    </div>
  )
}

// Conversion Analysis Component
const ConversionAnalysis = ({ conversions }) => {
  const [showAll, setShowAll] = useState(false)
  
  // Sort conversions by rate (highest first) and get top 4 most important ones
  const sortedConversions = [...conversions].sort((a, b) => b.rate - a.rate)
  const topConversions = sortedConversions.slice(0, 4)
  const remainingConversions = sortedConversions.slice(4)
  
  const renderConversionItem = (conversion, index) => (
    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
      <div className="flex-1">
        <div className="font-medium text-gray-900">{conversion.transition}</div>
        <div className="text-sm text-gray-600">
          {conversion.deals_moved} moved, {conversion.deals_dropped} dropped
        </div>
      </div>
      <div className="text-right">
        <div className={`text-lg font-bold ${conversion.rate >= 50 ? 'text-green-600' : conversion.rate >= 30 ? 'text-yellow-600' : 'text-red-600'}`}>
          {conversion.rate}%
        </div>
        <div className="text-xs text-gray-500">conversion</div>
      </div>
    </div>
  )

  return (
    <div className="space-y-3">
      {/* Top 4 Most Important Conversions */}
      {topConversions.map((conversion, index) => renderConversionItem(conversion, index))}
      
      {/* Show More/Less Button */}
      {remainingConversions.length > 0 && (
        <div>
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center justify-center w-full p-3 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors"
          >
            {showAll ? (
              <>
                <ChevronUp className="w-4 h-4 mr-2" />
                Show Less ({topConversions.length} of {conversions.length})
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 mr-2" />
                Show All Conversions ({remainingConversions.length} more)
              </>
            )}
          </button>
          
          {/* Remaining Conversions */}
          {showAll && (
            <div className="space-y-3 mt-3 border-t pt-3">
              {remainingConversions.map((conversion, index) => renderConversionItem(conversion, index + 4))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const problems = [
  { 
    id: 1, 
    title: 'Revenue Forecasting', 
    subtitle: 'Limited visibility on future revenues for planning',
    icon: TrendingUp, 
    color: 'blue' 
  },
  { 
    id: 2, 
    title: 'Deal Drop-off Analysis', 
    subtitle: 'No clear view of deal drop-offs across stages',
    icon: Target, 
    color: 'red' 
  },
  { 
    id: 3, 
    title: 'Effort vs Budget Tracking', 
    subtitle: 'Gaps in tracking actual effort vs budgeted, leading to overruns',
    icon: BarChart3, 
    color: 'green' 
  },
  { 
    id: 4, 
    title: 'Client Retention Insights', 
    subtitle: 'Lack of insight on client retention and repeat business',
    icon: Users, 
    color: 'purple' 
  },
  { 
    id: 5, 
    title: 'Data-Driven Hiring Decisions', 
    subtitle: 'Hiring and cost decisions are not data-driven',
    icon: Briefcase, 
    color: 'orange' 
  },
  { 
    id: 6, 
    title: 'Automation Opportunity Detection', 
    subtitle: 'Increasing efficiency in delivery operations',
    icon: Cpu, 
    color: 'indigo' 
  },
]

export default function ActionableItems() {
  const [selectedProblem, setSelectedProblem] = useState(1)
  const [actionableData, setActionableData] = useState(null)
  const [error, setError] = useState(null)

  const handleShareInsights = (problemTitle) => {
    toast.success(`Insights shared successfully with relevant stakeholders for ${problemTitle}`)
  }

  useEffect(() => {
    if (selectedProblem === 1 || selectedProblem === 2 || selectedProblem === 3 || selectedProblem === 4 || selectedProblem === 5 || selectedProblem === 6) {
      loadActionableItems(selectedProblem)
    } else {
      setActionableData(null)
    }
  }, [selectedProblem])

  const loadActionableItems = async (problemId) => {
    setError(null)
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8000/api/actionable-items/problem/${problemId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setActionableData(data)
    } catch (err) {
      console.error('Error loading actionable items:', err)
      setError(err.message)
    }
  }

  const getEmptyStateContent = (problemId) => {
    const problem = problems.find(p => p.id === problemId)
    return {
      title: `${problem.title} - Actionable Items`,
      description: `No actionable items generated yet for ${problem.title.toLowerCase()}.`,
      icon: problem.icon,
      color: problem.color
    }
  }

  const formatCurrency = (amount) => {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(1)}Cr`
    } else if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1)}L`
    } else {
      return `₹${amount.toLocaleString()}`
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-50 border-red-200 text-red-800'
      case 'medium': return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      case 'low': return 'bg-blue-50 border-blue-200 text-blue-800'
      default: return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'high': return AlertTriangle
      case 'medium': return Clock
      case 'low': return CheckCircle
      default: return CheckCircle
    }
  }

  const renderForecastSummary = (forecast) => {
    if (!forecast || Object.keys(forecast).length === 0) return null

    return (
      <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
          Revenue Forecast Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Next 3 Months</div>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(forecast.next_3_months || 0)}</div>
            <div className="text-xs text-gray-600">Confidence: {forecast.confidence || 0}%</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Next 6 Months</div>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(forecast.next_6_months || 0)}</div>
            <div className="text-xs text-gray-600">Confidence: {forecast.confidence || 0}%</div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Next 12 Months</div>
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(forecast.next_12_months || 0)}</div>
            <div className="text-xs text-gray-600">Confidence: {forecast.confidence || 0}%</div>
          </div>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          <strong>Model:</strong> {forecast.model_used || 'Unknown'} • {forecast.baseline_comparison || 'No comparison available'}
        </div>
      </div>
    )
  }

  const renderPipelineMetrics = (metrics) => {
    if (!metrics || Object.keys(metrics).length === 0) return null

  return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Activity className="w-5 h-5 mr-2 text-green-600" />
          Pipeline Health
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(metrics.pipeline_value || 0)}</div>
            <div className="text-sm text-gray-600">Pipeline Value</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{metrics.pipeline_count || 0}</div>
            <div className="text-sm text-gray-600">Active Deals</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{formatCurrency(metrics.avg_deal_size || 0)}</div>
            <div className="text-sm text-gray-600">Avg Deal Size</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${metrics.health_score >= 70 ? 'text-green-600' : metrics.health_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
              {metrics.health_score || 0}%
            </div>
            <div className="text-sm text-gray-600">Health Score</div>
          </div>
        </div>
        {metrics.stuck_deals_count > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="text-sm text-yellow-800">
              <strong>⚠️ {metrics.stuck_deals_count} deals</strong> have been stuck for 30+ days
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderActionableItems = (items) => {
    if (!items || items.length === 0) return null

    const groupedItems = items.reduce((acc, item) => {
      if (!acc[item.priority]) acc[item.priority] = []
      acc[item.priority].push(item)
      return acc
    }, {})

    const priorityOrder = ['high', 'medium', 'low']
    const priorityLabels = {
      high: 'High Priority',
      medium: 'Medium Priority', 
      low: 'Low Priority'
    }

    return (
      <div className="space-y-6">
        {priorityOrder.map(priority => {
          if (!groupedItems[priority]) return null
          
          const PriorityIcon = getPriorityIcon(priority)
          
                  return (
            <div key={priority}>
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <PriorityIcon className="w-5 h-5 mr-2" />
                {priorityLabels[priority]} ({groupedItems[priority].length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {groupedItems[priority].map((item, index) => (
                  <div key={item.id || index} className={`border rounded-lg p-4 ${getPriorityColor(priority)}`}>
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-gray-900">{item.title}</h4>
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${getPriorityColor(priority)}`}>
                        {item.priority.toUpperCase()}
                        </span>
                      </div>
                    <p className="text-sm text-gray-700">{item.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  const renderFunnelSummary = (summary) => {
    if (!summary || Object.keys(summary).length === 0) {
      return (
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="w-5 h-5 text-gray-600 mr-2" />
            Funnel Performance Overview
          </h3>
          <div className="text-center py-8">
            <div className="text-gray-500">No funnel data available</div>
            <div className="text-sm text-gray-400 mt-2">Please ensure your data files are properly uploaded</div>
          </div>
        </div>
      )
    }

    // Check if this is an early-stage stuck funnel
    const isEarlyStageStuck = summary.overall_conversion_rate < 5
    const earlyMetrics = actionableData?.early_stage_metrics


    // Standard funnel summary for proper progression data
    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Target className="w-5 h-5 text-blue-600 mr-2" />
          Funnel Performance Overview
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-blue-600">{summary.overall_conversion_rate}%</div>
            <div className="text-sm text-gray-600">Overall Conversion Rate</div>
            <div className="text-xs text-gray-500 mt-1">Lead to Won</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-green-600">{summary.total_active_deals}</div>
            <div className="text-sm text-gray-600">Active Deals</div>
            <div className="text-xs text-gray-500 mt-1">In Pipeline</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-purple-600">{summary.avg_sales_cycle_days}</div>
            <div className="text-sm text-gray-600">Avg Sales Cycle</div>
            <div className="text-xs text-gray-500 mt-1">Days</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-orange-600">{summary.stuck_deals_count}</div>
            <div className="text-sm text-gray-600">Stuck Deals</div>
            <div className="text-xs text-gray-500 mt-1">30+ Days</div>
          </div>
        </div>
        
        {summary.top_bottleneck && summary.top_bottleneck !== "No data available" && (
          <div className="mt-4 p-3 bg-orange-100 border border-orange-200 rounded-lg">
            <div className="flex items-center">
              <AlertTriangle className="w-4 h-4 text-orange-600 mr-2" />
              <span className="text-sm font-medium text-orange-800">
                Biggest Bottleneck: {summary.top_bottleneck}
              </span>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderConversionMetrics = (metrics) => {
    if (!metrics || Object.keys(metrics).length === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
          Conversion Analysis
        </h3>
        
        <div className="space-y-6">
          {/* Stage Conversions */}
          {metrics.stage_conversions && metrics.stage_conversions.length > 0 && (
            <div>
              <h4 className="text-md font-medium text-gray-800 mb-3">Stage-by-Stage Conversion</h4>
              <ConversionAnalysis conversions={metrics.stage_conversions} />
            </div>
          )}
          
        </div>
      </div>
    )
  }

  const renderAnalysisMethods = (methods) => {
    if (!methods || Object.keys(methods).length === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Activity className="w-5 h-5 text-purple-600 mr-2" />
          Analysis Methods & AI Techniques
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(methods).map(([key, method]) => (
            <div key={key} className="p-4 bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
              <div className="text-sm font-medium text-purple-800 mb-1 capitalize">
                {key.replace('_', ' ')}
              </div>
              <div className="text-sm text-gray-700">
                {method}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <strong>AI-Powered Insights:</strong> Our analysis combines statistical algorithms with Google Gemini LLM 
                to provide both quantitative metrics and human-like business recommendations. The system processes 
                stage progression data to identify conversion bottlenecks and generates actionable insights.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderVarianceSummary = (variance) => {
    if (!variance || Object.keys(variance).length === 0) return null

    const getVarianceColor = (pct) => {
      if (pct < 10) return 'text-green-600'
      if (pct < 20) return 'text-yellow-600'
      return 'text-red-600'
    }

    const getVarianceBgColor = (pct) => {
      if (pct < 10) return 'bg-green-50 border-green-200'
      if (pct < 20) return 'bg-yellow-50 border-yellow-200'
      return 'bg-red-50 border-red-200'
    }

    return (
      <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 text-green-600 mr-2" />
          Effort Variance Summary
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Total Projects</div>
            <div className="text-2xl font-bold text-gray-900">{variance.total_projects_analyzed || 0}</div>
            <div className="text-xs text-gray-600">Analyzed</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Overrun Projects</div>
            <div className="text-2xl font-bold text-red-600">{variance.overrun_projects || 0}</div>
            <div className="text-xs text-gray-600">{variance.overrun_rate || 0}% of total</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Avg Variance</div>
            <div className={`text-2xl font-bold ${getVarianceColor(variance.avg_variance_pct || 0)}`}>
              {variance.avg_variance_pct || 0}%
            </div>
            <div className="text-xs text-gray-600">Overrun</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-sm text-gray-500 mb-1">Total Variance</div>
            <div className="text-2xl font-bold text-gray-900">{(variance.total_variance_hours || 0).toLocaleString()}</div>
            <div className="text-xs text-gray-600">Hours</div>
          </div>
        </div>

        {variance.at_risk_projects && variance.at_risk_projects.length > 0 && (
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <h4 className="text-md font-semibold text-gray-800 mb-3">Top At-Risk Projects</h4>
            <div className="space-y-2">
              {variance.at_risk_projects.slice(0, 5).map((project, index) => (
                <div key={index} className={`p-3 rounded-lg border ${getVarianceBgColor(project.Variance_Percentage || 0)}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">Project {project['Project name'] || 'Unknown'}</div>
                      <div className="text-sm text-gray-600">
                        Planned: {project.Budgeted_Hours_Per_Month || 0} hrs • Actual: {project.Actual_Hours || 0} hrs
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${getVarianceColor(project.Variance_Percentage || 0)}`}>
                        {project.Variance_Percentage || 0}%
                      </div>
                      <div className="text-xs text-gray-500">{project.Status || 'Unknown'}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderBreakdownAnalysis = (breakdown) => {
    if (!breakdown || Object.keys(breakdown).length === 0) return null

    return (
      <div className="space-y-6">
        {/* Task Type Analysis */}
        {breakdown.by_task_type && breakdown.by_task_type.top_task_types && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Activity className="w-5 h-5 text-blue-600 mr-2" />
              Task Type Analysis
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {breakdown.by_task_type.top_task_types.slice(0, 6).map((task, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm font-medium text-gray-700 mb-1">{task.TaskType || 'Unknown'}</div>
                  <div className="text-2xl font-bold text-blue-600 mb-1">{task.Total_Hours || 0}</div>
                  <div className="text-xs text-gray-600">
                    {task.Project_Count || 0} projects • {task.Entry_Count || 0} entries
                  </div>
                </div>
              ))}
            </div>

            {breakdown.by_task_type.idle_time_analysis && breakdown.by_task_type.idle_time_analysis.total_idle_hours > 0 && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center">
                  <AlertTriangle className="w-4 h-4 text-yellow-600 mr-2" />
                  <span className="text-sm font-medium text-yellow-800">
                    Idle Time Alert: {breakdown.by_task_type.idle_time_analysis.total_idle_hours} hours across {breakdown.by_task_type.idle_time_analysis.idle_employees} employees
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Resource Analysis */}
        {breakdown.by_resource && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Users className="w-5 h-5 text-purple-600 mr-2" />
              Resource Utilization Analysis
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {breakdown.by_resource.high_efficiency && breakdown.by_resource.high_efficiency.length > 0 && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="text-sm font-medium text-green-800 mb-2">High Efficiency</div>
                  <div className="text-2xl font-bold text-green-600">{breakdown.by_resource.high_efficiency.length}</div>
                  <div className="text-xs text-green-700">Resources with &lt;10% idle time</div>
                </div>
              )}
              
              {breakdown.by_resource.low_efficiency && breakdown.by_resource.low_efficiency.length > 0 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="text-sm font-medium text-red-800 mb-2">Low Efficiency</div>
                  <div className="text-2xl font-bold text-red-600">{breakdown.by_resource.low_efficiency.length}</div>
                  <div className="text-xs text-red-700">Resources with &gt;30% idle time</div>
                </div>
              )}
              
              {breakdown.by_resource.underutilized && breakdown.by_resource.underutilized.length > 0 && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="text-sm font-medium text-yellow-800 mb-2">Underutilized</div>
                  <div className="text-2xl font-bold text-yellow-600">{breakdown.by_resource.underutilized.length}</div>
                  <div className="text-xs text-yellow-700">Resources with &gt;50% idle time</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderAnomalies = (anomalies) => {
    if (!anomalies || anomalies.detected_anomalies === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
          Anomaly Detection Results
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <div className="text-sm font-medium text-orange-800 mb-1">Anomalies Detected</div>
            <div className="text-2xl font-bold text-orange-600">{anomalies.detected_anomalies || 0}</div>
            <div className="text-xs text-orange-700">Projects flagged</div>
          </div>
          
          <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <div className="text-sm font-medium text-orange-800 mb-1">Anomaly Rate</div>
            <div className="text-2xl font-bold text-orange-600">{anomalies.anomaly_rate || 0}%</div>
            <div className="text-xs text-orange-700">Of total projects</div>
          </div>
          
          <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <div className="text-sm font-medium text-orange-800 mb-1">Method Used</div>
            <div className="text-lg font-bold text-orange-600">Isolation Forest</div>
            <div className="text-xs text-orange-700">ML-based detection</div>
          </div>
        </div>

        {anomalies.anomaly_details && anomalies.anomaly_details.length > 0 && (
          <div>
            <h4 className="text-md font-semibold text-gray-800 mb-3">Anomaly Details</h4>
            <div className="space-y-3">
              {anomalies.anomaly_details.slice(0, 3).map((anomaly, index) => (
                <div key={index} className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-medium text-gray-900">Project {anomaly.project_name || 'Unknown'}</div>
                      <div className="text-sm text-gray-600">{anomaly.explanation || 'Unusual pattern detected'}</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-sm font-bold ${anomaly.severity === 'Critical' ? 'text-red-600' : anomaly.severity === 'High' ? 'text-orange-600' : 'text-yellow-600'}`}>
                        {anomaly.severity || 'Low'}
                      </div>
                      <div className="text-xs text-gray-500">{anomaly.variance_pct || 0}% variance</div>
                    </div>
                  </div>
                  <div className="text-xs text-blue-600 font-medium">
                    Recommended: {anomaly.recommended_action || 'Monitor closely'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderRetentionSummary = (retention) => {
    if (!retention) return null

    const getRepeatRateColor = (rate) => {
      if (rate >= 60) return 'text-green-600'
      if (rate >= 40) return 'text-yellow-600'
      return 'text-red-600'
    }

    const getChurnRiskColor = (risk) => {
      if (risk <= 30) return 'text-green-600'
      if (risk <= 60) return 'text-yellow-600'
      return 'text-red-600'
    }

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center mb-6">
          <Users className="h-6 w-6 text-purple-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Client Retention Summary</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm font-medium text-blue-800 mb-1">Total Clients</div>
            <div className="text-2xl font-bold text-blue-600">{retention.total_clients_analyzed || 0}</div>
            <div className="text-xs text-blue-700">Analyzed for retention</div>
          </div>
          
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="text-sm font-medium text-green-800 mb-1">Repeat Business Rate</div>
            <div className={`text-2xl font-bold ${getRepeatRateColor(retention.repeat_business_rate || 0)}`}>
              {retention.repeat_business_rate?.toFixed(1) || 0}%
            </div>
            <div className="text-xs text-green-700">Clients with 2+ deals</div>
          </div>
          
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="text-sm font-medium text-purple-800 mb-1">Avg Time Between Deals</div>
            <div className="text-2xl font-bold text-purple-600">
              {retention.avg_time_between_deals ? Math.round(retention.avg_time_between_deals) : 0}
            </div>
            <div className="text-xs text-purple-700">Days</div>
          </div>
          
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="text-sm font-medium text-red-800 mb-1">At-Risk Clients</div>
            <div className={`text-2xl font-bold ${getChurnRiskColor(retention.avg_churn_risk || 0)}`}>
              {retention.at_risk_clients || 0}
            </div>
            <div className="text-xs text-red-700">High churn risk</div>
          </div>
        </div>
      </div>
    )
  }

  const renderAtRiskClients = (atRisk) => {
    if (!atRisk || atRisk.length === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4">
          <AlertTriangle className="h-6 w-6 text-red-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Top At-Risk Clients</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Churn Risk</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Deals</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Days Inactive</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Industry</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {atRisk.slice(0, 10).map((client, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {client.Client_Name || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      client.Churn_Risk_Score > 80 ? 'bg-red-100 text-red-800' :
                      client.Churn_Risk_Score > 60 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {client.Churn_Risk_Score?.toFixed(1) || 0}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {client.Deal_Count || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {client.Days_Since_Last_Activity || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {client.Industry_Type || 'Unknown'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  const renderSegmentationAnalysis = (segmentation) => {
    if (!segmentation) return null

    const industryData = segmentation.by_industry_size || {}
    const behaviorData = segmentation.by_behavior || {}

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4">
          <BarChart3 className="h-6 w-6 text-blue-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Client Segmentation Analysis</h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Industry & Size Segmentation */}
          <div>
            <h4 className="text-md font-medium text-gray-800 mb-3">By Industry & Size</h4>
            <div className="space-y-2">
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-sm font-medium text-blue-800">Top Industry</div>
                <div className="text-lg font-bold text-blue-600">{industryData.top_industry || 'Unknown'}</div>
              </div>
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="text-sm font-medium text-green-800">Top Size Category</div>
                <div className="text-lg font-bold text-green-600">{industryData.top_size_category || 'Unknown'}</div>
              </div>
              <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <div className="text-sm font-medium text-purple-800">Total Segments</div>
                <div className="text-lg font-bold text-purple-600">{industryData.total_segments || 0}</div>
              </div>
            </div>
          </div>

          {/* Behavioral Segmentation */}
          <div>
            <h4 className="text-md font-medium text-gray-800 mb-3">By Behavior</h4>
            <div className="space-y-2">
              <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                <div className="text-sm font-medium text-orange-800">High-Value Frequent</div>
                <div className="text-lg font-bold text-orange-600">{behaviorData.high_value_frequent || 0}</div>
              </div>
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="text-sm font-medium text-yellow-800">Quick Converters</div>
                <div className="text-lg font-bold text-yellow-600">{behaviorData.quick_converters || 0}</div>
              </div>
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="text-sm font-medium text-red-800">One-Time Buyers</div>
                <div className="text-lg font-bold text-red-600">{behaviorData.one_time_buyers || 0}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderRepeatPatterns = (patterns) => {
    if (!patterns) return null

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center mb-4">
          <TrendingUp className="h-6 w-6 text-green-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Repeat Business Patterns</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="text-sm font-medium text-green-800 mb-1">Repeat Clients</div>
            <div className="text-2xl font-bold text-green-600">{patterns.repeat_clients || 0}</div>
            <div className="text-xs text-green-700">out of {patterns.total_clients || 0} total</div>
          </div>
          
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-sm font-medium text-blue-800 mb-1">High-Value Repeat</div>
            <div className="text-2xl font-bold text-blue-600">{patterns.high_value_repeat || 0}</div>
            <div className="text-xs text-blue-700">Top revenue clients</div>
          </div>
          
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="text-sm font-medium text-purple-800 mb-1">Quick Repeaters</div>
            <div className="text-2xl font-bold text-purple-600">{patterns.quick_repeaters || 0}</div>
            <div className="text-xs text-purple-700">≤6 months between deals</div>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="text-sm text-gray-600">
            <strong>Average deals per client:</strong> {patterns.avg_deals_per_client?.toFixed(1) || 0}
          </div>
        </div>
      </div>
    )
  }

  const renderAutomationSummary = (summary) => {
    if (!summary || Object.keys(summary).length === 0) return null

    const automationPercentage = summary.automation_percentage || 0
    const bgColor = automationPercentage >= 40 ? 'from-green-50 to-emerald-50 border-green-200' : 
                   automationPercentage >= 20 ? 'from-yellow-50 to-orange-50 border-yellow-200' : 
                   'from-red-50 to-pink-50 border-red-200'

    return (
      <div className={`bg-gradient-to-r ${bgColor} border rounded-lg p-6 mb-6`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Cpu className="w-5 h-5 text-blue-600 mr-2" />
          Automation Opportunity Summary
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-blue-600">{summary.total_tasks_analyzed || 0}</div>
            <div className="text-sm text-gray-600">Total Tasks Analyzed</div>
            <div className="text-xs text-gray-500 mt-1">Unique task types</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-green-600">{summary.automation_percentage?.toFixed(1) || 0}%</div>
            <div className="text-sm text-gray-600">Automation Potential</div>
            <div className="text-xs text-gray-500 mt-1">% of tasks automatable</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-orange-600">{summary.potential_monthly_savings?.toFixed(0) || 0}</div>
            <div className="text-sm text-gray-600">Hours Savable/Month</div>
            <div className="text-xs text-gray-500 mt-1">Potential time savings</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-purple-600">{summary.high_priority_tasks || 0}</div>
            <div className="text-sm text-gray-600">High Priority Tasks</div>
            <div className="text-xs text-gray-500 mt-1">Immediate automation wins</div>
          </div>
        </div>
      </div>
    )
  }

  const renderTaskClusters = (tasks) => {
    if (!tasks || tasks.length === 0) return null

    return (
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h4 className="font-semibold text-gray-800">Task Automation Opportunities</h4>
          <p className="text-sm text-gray-600">Scroll to view all tasks</p>
        </div>
        <div className="max-h-64 overflow-y-auto">
          {tasks.map((task, index) => (
            <div key={index} className="p-3 border-b last:border-b-0 hover:bg-gray-50">
              <div className="flex justify-between items-center">
                <div>
                  <h5 className="font-medium text-gray-800">{task.name}</h5>
                  <p className="text-sm text-gray-600">
                    {task.frequency} • {task.time_spent}h/week
                  </p>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    task.automation_potential === 'High' ? 'bg-green-100 text-green-800' :
                    task.automation_potential === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {task.automation_potential}
                  </span>
                  <div className="text-xs text-gray-500 mt-1">{task.roi}% ROI</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderTopCandidates = (candidates) => {
    if (!candidates || candidates.length === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Star className="w-5 h-5 text-yellow-600 mr-2" />
          Top Automation Candidates
        </h3>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Task</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Frequency</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hours/Month</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Approach</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {candidates.slice(0, 10).map((candidate, index) => {
                const score = candidate.automation_score || 0
                const scoreColor = score >= 75 ? 'text-green-600 bg-green-100' : 
                                 score >= 50 ? 'text-yellow-600 bg-yellow-100' : 
                                 'text-red-600 bg-red-100'
                
                return (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{candidate.task_name || 'Unknown'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-600">{candidate.task_type || 'Unknown'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-600">{candidate.avg_monthly_frequency?.toFixed(1) || 0}/month</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-600">{candidate.monthly_hours?.toFixed(1) || 0}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${scoreColor}`}>
                        {score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-600">{candidate.automation_type || 'General'}</div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  const renderAutomationBreakdown = (breakdown) => {
    if (!breakdown || breakdown.length === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <PieChart className="w-5 h-5 text-indigo-600 mr-2" />
          Automation Type Breakdown
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {breakdown.map((item, index) => {
            const typeColors = {
              'RPA': 'bg-blue-100 text-blue-800',
              'API': 'bg-green-100 text-green-800',
              'Script': 'bg-yellow-100 text-yellow-800',
              'Process': 'bg-purple-100 text-purple-800',
              'General': 'bg-gray-100 text-gray-800'
            }
            
            return (
              <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-900">{item.automation_type || 'Unknown'}</h4>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${typeColors[item.automation_type] || typeColors['General']}`}>
                    {item.automation_type || 'General'}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tasks:</span>
                    <span className="font-medium">{item.task_count || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Hours/Month:</span>
                    <span className="font-medium">{item.total_hours?.toFixed(1) || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Score:</span>
                    <span className="font-medium">{item.avg_score?.toFixed(1) || 0}/100</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderROIAnalysis = (roi) => {
    if (!roi || Object.keys(roi).length === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
          ROI Analysis
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="text-2xl font-bold text-blue-600">{roi.total_monthly_hours?.toFixed(0) || 0}</div>
            <div className="text-sm text-gray-600">Total Monthly Hours</div>
            <div className="text-xs text-gray-500 mt-1">Current effort across all tasks</div>
          </div>
          
          <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="text-2xl font-bold text-green-600">{roi.total_potential_savings?.toFixed(0) || 0}</div>
            <div className="text-sm text-gray-600">Potential Monthly Savings</div>
            <div className="text-xs text-gray-500 mt-1">Hours that could be automated</div>
          </div>
          
          <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
            <div className="text-2xl font-bold text-purple-600">{roi.automation_percentage?.toFixed(1) || 0}%</div>
            <div className="text-sm text-gray-600">Automation Percentage</div>
            <div className="text-xs text-gray-500 mt-1">% of total effort automatable</div>
          </div>
        </div>
        
        {roi.savings_by_type && roi.savings_by_type.length > 0 && (
          <div className="mt-6">
            <h4 className="text-md font-semibold text-gray-900 mb-3">Savings by Automation Type</h4>
            <div className="space-y-2">
              {roi.savings_by_type.map((saving, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                  <span className="text-sm font-medium text-gray-700">{saving.automation_type || 'Unknown'}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">{saving.estimated_monthly_savings?.toFixed(1) || 0} hrs/month</span>
                    <span className="text-xs text-gray-500">({(saving.savings_potential * 100)?.toFixed(0) || 0}% potential)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderHiringSummary = (summary) => {
    if (!summary || Object.keys(summary).length === 0) return null

    const employeesNeeded = summary.total_employees_needed || 0
    const totalCost = summary.total_hiring_cost || 0
    const capacityUtilization = summary.current_capacity_utilization || 0
    
    const bgColor = employeesNeeded > 0 ? 'from-blue-50 to-indigo-50 border-blue-200' : 'from-green-50 to-emerald-50 border-green-200'

    return (
      <div className={`bg-gradient-to-r ${bgColor} border rounded-lg p-6 mb-6`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Briefcase className="w-5 h-5 text-orange-600 mr-2" />
          Hiring Forecast Summary
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-orange-600">{employeesNeeded}</div>
            <div className="text-sm text-gray-600">Employees Needed</div>
            <div className="text-xs text-gray-500 mt-1">Recommended hiring</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-blue-600">${(totalCost / 1000).toFixed(0)}K</div>
            <div className="text-sm text-gray-600">Total Hiring Cost</div>
            <div className="text-xs text-gray-500 mt-1">Annual investment</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-green-600">{capacityUtilization.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Capacity Utilization</div>
            <div className="text-xs text-gray-500 mt-1">Current workload</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-2xl font-bold text-purple-600">{summary.roi_percentage?.toFixed(1) || 0}%</div>
            <div className="text-sm text-gray-600">Expected ROI</div>
            <div className="text-xs text-gray-500 mt-1">Return on investment</div>
          </div>
        </div>
      </div>
    )
  }

  const renderWorkloadAnalysis = (workload) => {
    if (!workload || Object.keys(workload).length === 0) return null

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Activity className="w-5 h-5 text-blue-600 mr-2" />
          Workload & Capacity Analysis
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="text-2xl font-bold text-blue-600">{workload.avg_monthly_hours?.toFixed(0) || 0}</div>
            <div className="text-sm text-gray-600">Avg Monthly Hours</div>
            <div className="text-xs text-gray-500 mt-1">Total team effort</div>
          </div>
          
          <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="text-2xl font-bold text-green-600">{workload.avg_employees?.toFixed(1) || 0}</div>
            <div className="text-sm text-gray-600">Average Employees</div>
            <div className="text-xs text-gray-500 mt-1">Active team size</div>
          </div>
          
          <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
            <div className="text-2xl font-bold text-orange-600">{workload.avg_hours_per_employee?.toFixed(1) || 0}</div>
            <div className="text-sm text-gray-600">Hours per Employee</div>
            <div className="text-xs text-gray-500 mt-1">Individual workload</div>
          </div>
        </div>
        
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">Trend Analysis</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Hours Trend:</span>
                <span className={`font-medium ${(workload.hours_trend || 0) > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(workload.hours_trend || 0).toFixed(1)}% per month
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Employee Trend:</span>
                <span className={`font-medium ${(workload.employee_trend || 0) > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(workload.employee_trend || 0).toFixed(1)}% per month
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Months Analyzed:</span>
                <span className="font-medium">{workload.total_months_analyzed || 0}</span>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">Capacity Metrics</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Utilization:</span>
                <span className={`font-medium ${(workload.capacity_utilization || 0) > 80 ? 'text-red-600' : (workload.capacity_utilization || 0) > 60 ? 'text-yellow-600' : 'text-green-600'}`}>
                  {(workload.capacity_utilization || 0).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className={`font-medium ${(workload.capacity_utilization || 0) > 80 ? 'text-red-600' : (workload.capacity_utilization || 0) > 60 ? 'text-yellow-600' : 'text-green-600'}`}>
                  {(workload.capacity_utilization || 0) > 80 ? 'Overloaded' : (workload.capacity_utilization || 0) > 60 ? 'Moderate' : 'Underutilized'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderSkillAnalysis = (skillAnalysis) => {
    if (!skillAnalysis || Object.keys(skillAnalysis).length === 0) return null

    const skillGaps = skillAnalysis.skill_gaps || []
    const highDemandSkills = skillAnalysis.high_demand_skills || []

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Users className="w-5 h-5 text-purple-600 mr-2" />
          Skill Demand & Gap Analysis
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">High Demand Skills</h4>
            <div className="space-y-2">
              {highDemandSkills.slice(0, 5).map((skill, index) => (
                <div key={index} className="flex items-center justify-between bg-white rounded-lg p-2">
                  <span className="text-sm font-medium text-gray-700">{skill}</span>
                  <span className="text-xs text-gray-500">High Demand</span>
                </div>
              ))}
              {highDemandSkills.length === 0 && (
                <div className="text-sm text-gray-500">No high demand skills identified</div>
              )}
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">Critical Skill Gaps</h4>
            <div className="space-y-2">
              {skillGaps.slice(0, 5).map((gap, index) => (
                <div key={index} className="bg-white rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{gap.skill}</span>
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      gap.demand_level === 'High' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {gap.demand_level}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {gap.avg_hours_per_employee?.toFixed(1) || 0} hrs/employee
                  </div>
                </div>
              ))}
              {skillGaps.length === 0 && (
                <div className="text-sm text-gray-500">No critical skill gaps identified</div>
              )}
            </div>
          </div>
        </div>
        
        <div className="mt-4 text-center">
          <div className="text-sm text-gray-600">
            <strong>Total Skill Types:</strong> {skillAnalysis.total_skill_types || 0}
          </div>
        </div>
      </div>
    )
  }

  const renderHiringForecast = (forecast) => {
    if (!forecast || Object.keys(forecast).length === 0) return null

    const scenarios = Object.entries(forecast).filter(([key, _]) => key !== 'overall_recommendation')
    const overall = forecast.overall_recommendation || {}

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 text-green-600 mr-2" />
          Hiring Forecast Scenarios
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {scenarios.map(([key, scenario], index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900 text-sm">{scenario.name}</h4>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                  scenario.priority === 'High' ? 'bg-red-100 text-red-800' :
                  scenario.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {scenario.priority}
                </span>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Employees:</span>
                  <span className="font-medium">{scenario.additional_employees_needed || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Timeline:</span>
                  <span className="font-medium">{scenario.timeline || 'Unknown'}</span>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="text-xs text-gray-500">{scenario.reasoning}</div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
          <h4 className="font-medium text-gray-900 mb-3">Overall Recommendation</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{overall.total_employees_needed || 0}</div>
              <div className="text-sm text-gray-600">Total Employees Needed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{overall.priority || 'Low'}</div>
              <div className="text-sm text-gray-600">Priority Level</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{overall.timeline || 'No immediate need'}</div>
              <div className="text-sm text-gray-600">Recommended Timeline</div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderCostAnalysis = (costAnalysis) => {
    if (!costAnalysis || Object.keys(costAnalysis).length === 0) return null

    const costBreakdown = costAnalysis.cost_breakdown || []

    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <DollarSign className="w-5 h-5 text-green-600 mr-2" />
          Cost Analysis & ROI
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="text-2xl font-bold text-green-600">${(costAnalysis.total_hiring_cost / 1000)?.toFixed(0) || 0}K</div>
            <div className="text-sm text-gray-600">Total Hiring Cost</div>
            <div className="text-xs text-gray-500 mt-1">Annual investment</div>
          </div>
          
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="text-2xl font-bold text-blue-600">${(costAnalysis.cost_per_employee / 1000)?.toFixed(0) || 0}K</div>
            <div className="text-sm text-gray-600">Cost per Employee</div>
            <div className="text-xs text-gray-500 mt-1">Average cost</div>
          </div>
          
          <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
            <div className="text-2xl font-bold text-purple-600">{costAnalysis.roi_percentage?.toFixed(1) || 0}%</div>
            <div className="text-sm text-gray-600">Expected ROI</div>
            <div className="text-xs text-gray-500 mt-1">Return on investment</div>
          </div>
        </div>
        
        {costBreakdown.length > 0 && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3">Cost Breakdown</h4>
            <div className="space-y-2">
              {costBreakdown.map((item, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                  <span className="text-sm font-medium text-gray-700">{item.category}</span>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">${(item.total_cost / 1000)?.toFixed(0) || 0}K</span>
                    <span className="text-xs text-gray-500">({item.percentage?.toFixed(0) || 0}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderProjectList = (projects) => {
    if (!projects || projects.length === 0) return null

    return (
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h4 className="font-semibold text-gray-800">Project Budget Status</h4>
          <p className="text-sm text-gray-600">Scroll to view all projects</p>
        </div>
        <div className="max-h-64 overflow-y-auto">
          {projects.map((project, index) => (
            <div key={index} className="p-3 border-b last:border-b-0 hover:bg-gray-50">
              <div className="flex justify-between items-center">
                <div>
                  <h5 className="font-medium text-gray-800">{project.name}</h5>
                  <p className="text-sm text-gray-600">
                    Budgeted: {project.budgeted}h | Actual: {project.actual}h
                  </p>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    project.variance > 20 ? 'bg-red-100 text-red-800' :
                    project.variance > 0 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {project.variance > 0 ? '+' : ''}{project.variance}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderStuckDeals = (deals) => {
    if (!deals || deals.length === 0) return null

    // Calculate actual metrics from the deals data
    const actualDeals = deals.filter(deal => deal.value > 0)
    const totalValue = actualDeals.reduce((sum, deal) => sum + deal.value, 0)
    const avgDays = actualDeals.length > 0 ? Math.round(actualDeals.reduce((sum, deal) => sum + deal.days_stuck, 0) / actualDeals.length) : 0

    return (
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h4 className="font-semibold text-gray-800">Stuck Deals - Pipeline Analysis</h4>
          <p className="text-sm text-gray-600">
            {actualDeals.length > 0 
              ? `${actualDeals.length} deals worth $${(totalValue/1000000).toFixed(1)}M stuck for ${avgDays}+ days on average`
              : "No deals currently stuck for 30+ days"
            }
          </p>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {deals.map((deal, index) => (
            <div key={index} className="p-4 border-b last:border-b-0 hover:bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h5 className="font-semibold text-gray-900 text-lg">{deal.client}</h5>
                  <p className="text-sm text-gray-600">Contact: {deal.contact}</p>
                  <p className="text-xs text-gray-500">Stage: {deal.stage} | Deal ID: {deal.deal_id}</p>
                </div>
                <div className="text-right ml-4">
                  <div className="text-lg font-bold text-red-600">${(deal.value / 1000).toFixed(0)}K</div>
                  <div className="text-sm text-gray-500">{deal.days_stuck} days stuck</div>
                </div>
              </div>
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-sm text-blue-800">
                  <span className="font-medium">Client Expectation:</span> {deal.expectation}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }


  const renderVisualization = (viz) => {
    return null // Visualizations removed as per plan
  }

  const renderContent = () => {

    if (error) {
      return (
        <div className="bg-white rounded-lg shadow-lg p-12">
          <div className="text-center">
            <AlertTriangle className="w-8 h-8 mx-auto text-red-500 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Data</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => loadActionableItems(selectedProblem)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Try Again
            </button>
              </div>
            </div>
      )
    }

    if (selectedProblem === 1 && actionableData) {
      return (
        <div className="space-y-6">
          {renderForecastSummary(actionableData.forecast_summary)}
          {renderPipelineMetrics(actionableData.pipeline_metrics)}
          {actionableData.ai_insights && (
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
              {formatAIInsights(actionableData.ai_insights)}
            </div>
          )}
          {renderStuckDeals(actionableData.stuck_deals)}
          {renderActionableItems(actionableData.actionable_items)}
          
          {/* Share Button */}
          <div className="flex justify-end">
            <button
              onClick={() => handleShareInsights('Revenue Forecasting')}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Mail className="w-4 h-4 mr-2" />
              Share Insights
            </button>
          </div>
        </div>
      )
    }

  if (selectedProblem === 2 && actionableData) {
    return (
      <div className="space-y-6">
        {renderFunnelSummary(actionableData.funnel_summary)}
        {renderAnalysisMethods(actionableData.funnel_summary?.analysis_methods)}
        {renderConversionMetrics(actionableData.conversion_metrics)}
        {actionableData.ai_insights && (
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
            {formatAIInsights(actionableData.ai_insights)}
          </div>
        )}
        {renderActionableItems(actionableData.actionable_items)}
        
        {/* Share Button */}
        <div className="flex justify-end">
          <button
            onClick={() => handleShareInsights('Deal Drop-off Analysis')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Mail className="w-4 h-4 mr-2" />
            Share Insights
          </button>
        </div>
      </div>
    )
  }

  if (selectedProblem === 2 && !actionableData) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Deal Drop-off Analysis</h3>
          <div className="text-center py-8">
            <div className="text-gray-500">Loading analysis...</div>
            <div className="text-sm text-gray-400 mt-2">This may take a few moments</div>
          </div>
        </div>
      </div>
    )
  }

    if (selectedProblem === 3 && actionableData) {
      return (
        <div className="space-y-6">
          {renderVarianceSummary(actionableData.variance_summary)}
          {actionableData.ai_insights && (
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
              {formatAIInsights(actionableData.ai_insights)}
            </div>
          )}
          {renderProjectList(actionableData.project_list)}
          {renderActionableItems(actionableData.actionable_items)}
          
          {/* Share Button */}
          <div className="flex justify-end">
            <button
              onClick={() => handleShareInsights('Effort vs Budget Tracking')}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Mail className="w-4 h-4 mr-2" />
              Share Insights
            </button>
          </div>
        </div>
      )
    }

    if (selectedProblem === 4 && actionableData) {
      return (
        <div className="space-y-6">
          {renderRetentionSummary(actionableData.retention_summary)}
          {renderAtRiskClients(actionableData.at_risk_clients)}
          {actionableData.ai_insights && (
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
              {formatAIInsights(actionableData.ai_insights)}
            </div>
          )}
          {renderActionableItems(actionableData.actionable_items)}
          
          {/* Share Button */}
          <div className="flex justify-end">
            <button
              onClick={() => handleShareInsights('Client Retention Insights')}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Mail className="w-4 h-4 mr-2" />
              Share Insights
            </button>
          </div>
        </div>
      )
    }

    if (selectedProblem === 5 && actionableData) {
      return (
        <div className="space-y-6">
          {renderHiringSummary(actionableData.hiring_summary)}
          {actionableData.ai_insights && (
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
              {formatAIInsights(actionableData.ai_insights)}
            </div>
          )}
          {renderActionableItems(actionableData.actionable_items)}
          
          {/* Share Button */}
          <div className="flex justify-end">
            <button
              onClick={() => handleShareInsights('Data-Driven Hiring Decisions')}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Mail className="w-4 h-4 mr-2" />
              Share Insights
            </button>
          </div>
        </div>
      )
    }

    if (selectedProblem === 6 && actionableData) {
      return (
        <div className="space-y-6">
          {renderAutomationSummary(actionableData.automation_summary)}
          {actionableData.ai_insights && (
            <div className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Powered Insights</h3>
              {formatAIInsights(actionableData.ai_insights)}
            </div>
          )}
          {renderTaskClusters(actionableData.task_clusters)}
          {renderActionableItems(actionableData.actionable_items)}
          
          {/* Share Button */}
          <div className="flex justify-end">
            <button
              onClick={() => handleShareInsights('Automation Opportunity Detection')}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Mail className="w-4 h-4 mr-2" />
              Share Insights
            </button>
          </div>
        </div>
      )
    }

    // Empty state for other problems
    const emptyState = getEmptyStateContent(selectedProblem)
    const Icon = emptyState.icon

    return (
      <div className="bg-white rounded-lg shadow-lg p-12">
        <div className="text-center">
          <div className={`mx-auto w-16 h-16 bg-${emptyState.color}-100 rounded-full flex items-center justify-center mb-6`}>
            <Icon className={`w-8 h-8 text-${emptyState.color}-600`} />
          </div>
          
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {emptyState.title}
          </h2>
          
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            {emptyState.description}
          </p>

          <div className="bg-gray-50 rounded-lg p-6 max-w-2xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center justify-center">
              <Clock className="w-5 h-5 mr-2 text-gray-500" />
              Coming Soon
            </h3>
            <p className="text-gray-600 text-sm">
              Actionable items will be generated based on your data analysis and AI insights. 
              This will include prioritized recommendations, implementation timelines, and expected outcomes.
            </p>
              </div>

          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
            <div className="bg-blue-50 rounded-lg p-4">
              <CheckCircle className="w-6 h-6 text-blue-600 mx-auto mb-2" />
              <h4 className="font-semibold text-blue-900 mb-1">Prioritized Actions</h4>
              <p className="text-blue-700 text-sm">High-impact recommendations ranked by urgency and potential ROI</p>
            </div>
            
            <div className="bg-green-50 rounded-lg p-4">
              <Clock className="w-6 h-6 text-green-600 mx-auto mb-2" />
              <h4 className="font-semibold text-green-900 mb-1">Implementation Plans</h4>
              <p className="text-green-700 text-sm">Step-by-step action plans with timelines and resource requirements</p>
              </div>
            
            <div className="bg-purple-50 rounded-lg p-4">
              <AlertTriangle className="w-6 h-6 text-purple-600 mx-auto mb-2" />
              <h4 className="font-semibold text-purple-900 mb-1">Impact Assessment</h4>
              <p className="text-purple-700 text-sm">Expected outcomes, risk analysis, and success metrics</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Actionable Items</h1>
          <p className="mt-2 text-gray-600">Problem-specific recommendations and action plans</p>
        </div>
      </div>

      {/* Problem Selection Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {problems.map((problem) => {
              const ProblemIcon = problem.icon
              const isActive = selectedProblem === problem.id
              return (
                <button
                  key={problem.id}
                  onClick={() => setSelectedProblem(problem.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex flex-col items-start space-y-1 ${
                    isActive
                      ? `border-${problem.color}-500 text-${problem.color}-600`
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <ProblemIcon className="w-4 h-4" />
                    <span>{problem.title}</span>
                  </div>
                  <div className="text-xs text-gray-400 max-w-48 text-left">
                    {problem.subtitle}
                  </div>
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Content */}
      {renderContent()}
    </div>
  )
}

