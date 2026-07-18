import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App Root Component', () => {
  it('is exported as a React functional component', () => {
    expect(typeof App).toBe('function');
  });
});
