import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-black p-4">
          <div className="max-w-md w-full bg-gray-900 border border-red-500/50 rounded-3xl p-8 text-center shadow-2xl">
            <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">⚠️</span>
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">Something went wrong</h1>
            <p className="text-gray-400 mb-8 leading-relaxed">
              We encountered an unexpected error. This usually happens when the connection is interrupted or data is malformed.
            </p>
            <div className="bg-black/40 rounded-2xl p-4 mb-8 text-left overflow-auto max-h-40 border border-gray-800">
              <code className="text-red-400 text-sm whitespace-pre-wrap">
                {this.state.error?.toString()}
              </code>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-2xl transition-all active:scale-[0.98]"
            >
              Refresh Page
            </button>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-4 text-gray-500 hover:text-gray-400 text-sm font-medium"
            >
              Dismiss and try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
