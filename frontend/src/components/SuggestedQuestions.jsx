export default function SuggestedQuestions({ suggestions, onSelect }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        💡 Suggested Questions
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSelect(suggestion)}
            className="text-left p-3 bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-lg transition text-sm text-gray-700 hover:text-blue-700"
          >
            <span className="mr-2">→</span>
            {suggestion}
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-4">
        Click any question to get started, or type your own question below
      </p>
    </div>
  );
}


