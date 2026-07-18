import { describe, it, expect, vi } from 'vitest';
import { ErrorBoundary } from '../components/ErrorBoundary';

describe('ErrorBoundary class logic', () => {
  it('updates state when an error is caught by getDerivedStateFromError', () => {
    const error = new Error('Test crash error');
    const nextState = ErrorBoundary.getDerivedStateFromError(error);
    expect(nextState).toEqual({ hasError: true, error });
  });

  it('sets initial state correctly', () => {
    const inst = new ErrorBoundary({});
    expect(inst.state).toEqual({ hasError: false, error: null });
  });

  it('logs the error in componentDidCatch', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const inst = new ErrorBoundary({});
    const error = new Error('Catch Error');
    const info = { componentStack: 'broken stack' };

    inst.componentDidCatch(error, info);

    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining('ErrorBoundary caught an unhandled error:'),
      error,
      info
    );

    spy.mockRestore();
  });
});
