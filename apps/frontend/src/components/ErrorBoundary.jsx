import React, { Component } from 'react';

/**
 * React Error Boundary component to catch and recover from UI component crashes.
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="error-container" style={{ padding: '2rem', textAlign: 'center', background: '#131928', border: '1px solid #1e2d47', borderRadius: '8px', color: '#f3f4f6', margin: '2rem auto', maxWidth: '500px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.75rem' }}>Something went wrong</h2>
          <p style={{ color: '#8a9bb8', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
            {this.state.error?.message || 'An unexpected frontend error occurred.'}
          </p>
          <button
            className="btn btn-primary"
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
