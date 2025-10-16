export default function DataQualityCard({ qualityScore, issues = [] }) {
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    return 'Needs Attention';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Data Quality</h3>
      
      <div className="flex items-center gap-3 mb-3">
        <div className="flex-1">
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold ${getScoreColor(qualityScore)}`}>
              {qualityScore}
            </span>
            <span className="text-sm text-gray-500">/ 100</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">{getScoreLabel(qualityScore)}</p>
        </div>

        <div className="w-16 h-16">
          <svg className="transform -rotate-90" viewBox="0 0 36 36">
            <circle
              cx="18"
              cy="18"
              r="16"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="3"
            />
            <circle
              cx="18"
              cy="18"
              r="16"
              fill="none"
              stroke={qualityScore >= 80 ? '#10b981' : qualityScore >= 60 ? '#f59e0b' : '#ef4444'}
              strokeWidth="3"
              strokeDasharray={`${qualityScore} 100`}
              strokeLinecap="round"
            />
          </svg>
        </div>
      </div>

      {issues.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs font-semibold text-gray-700 mb-1">Issues:</p>
          <ul className="text-xs text-gray-600 space-y-1">
            {issues.slice(0, 3).map((issue, index) => (
              <li key={index}>• {issue}</li>
            ))}
            {issues.length > 3 && (
              <li className="text-blue-600">+ {issues.length - 3} more</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}


