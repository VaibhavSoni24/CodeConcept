import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("UI Rendering Error caught by global boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-12 h-full text-center slide-up">
          <div className="bg-red-500/10 text-red-400 p-8 rounded-xl max-w-lg border border-red-500/30">
            <h2 className="text-xl font-bold mb-4">Something went wrong</h2>
            <p className="text-sm opacity-80 mb-4">
              We encountered an issue rendering this view. Please try refreshing or submit feedback if the issue persists.
            </p>
            <div className="bg-black/30 p-4 rounded text-xs text-left overflow-x-auto text-red-300 font-mono">
              {this.state.error?.toString()}
            </div>
            <button 
              className="mt-6 px-4 py-2 bg-[var(--bg-secondary)] hover:bg-[var(--bg-card)] border border-[var(--border)] rounded text-[var(--text-primary)] transition-colors"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children; 
  }
}

export default ErrorBoundary;
