import { useContext } from 'react';
import { AuthCtx } from '../AuthCtx';

/**
 * Custom React hook to access authentication state and helper actions.
 */
export const useAuth = () => {
  const context = useContext(AuthCtx);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
