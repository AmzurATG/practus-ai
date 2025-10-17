import { useState, useEffect } from 'react';
import { getApiUrl } from '../config/api';

export default function ActionCenter() {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActions();
  }, []);

  const loadActions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(getApiUrl('/api/actions/recommended'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setActions(data.actions || []);
    } catch (error) {
      console.error('Error loading actions:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeAction = async (actionId) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(getApiUrl('/api/actions/execute'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ action_id: actionId })
      });
      
      // Reload actions
      loadActions();
    } catch (error) {
      console.error('Error executing action:', error);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '💡';
      default: return '📋';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Action Center</h2>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">
          Action Center
        </h2>
        <span className="text-sm text-gray-600">
          {actions.length} {actions.length === 1 ? 'action' : 'actions'} recommended
        </span>
      </div>

      {actions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>✓ All caught up! No urgent actions at the moment.</p>
          <p className="text-sm mt-2">AI is monitoring your business 24/7</p>
        </div>
      ) : (
        <div className="space-y-3">
          {actions.map((action, index) => (
            <div
              key={action.action_id || index}
              className={`border-2 rounded-lg p-4 ${getPriorityColor(action.priority)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{getPriorityIcon(action.priority)}</span>
                    <h3 className="font-semibold text-gray-900">
                      {action.title}
                    </h3>
                    <span className={`text-xs px-2 py-1 rounded ${
                      action.priority === 'urgent' ? 'bg-red-200' :
                      action.priority === 'high' ? 'bg-orange-200' :
                      action.priority === 'medium' ? 'bg-yellow-200' :
                      'bg-gray-200'
                    }`}>
                      {action.priority.toUpperCase()}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-700 mb-2">
                    {action.description}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span>💰 Impact: {action.impact?.description || 'High'}</span>
                    <span>⏱️ Effort: {action.effort}</span>
                    <span>📊 Score: {action.priority_score}</span>
                  </div>

                  {action.deadline && (
                    <div className="mt-2 text-xs text-gray-600">
                      ⏰ Deadline: {action.deadline}
                    </div>
                  )}
                </div>

                <div className="ml-4 flex flex-col gap-2">
                  <button
                    onClick={() => executeAction(action.action_id)}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                  >
                    Execute
                  </button>
                  {action.template && (
                    <button className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 transition">
                      View Template
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t">
        <button
          onClick={loadActions}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          🔄 Refresh Actions
        </button>
      </div>
    </div>
  );
}


