# Contributing to ArenaIQ

Thank you for contributing to ArenaIQ! To ensure a high standard of quality, accessibility, and security across the platform, please review and adhere to the guidelines below.

## Code Quality Standards

1. **Linting and Formatting**:
   - Python code must comply with Ruff rules defined in `pyproject.toml`. Run `ruff check app/ tests/` before committing.
   - Frontend JavaScript must follow Prettier rules and pass `oxlint` checks. Run `npm run lint`.
2. **Type Annotations**:
   - Python code should utilize explicit type annotations wherever possible. Run `mypy app/` to verify types.
   - React components must be documented with complete JSDoc headers specifying parameter and return types.

## Development Workflow

1. **Branch Naming**:
   - Feature branches: `feat/feature-name`
   - Bug fixes: `fix/bug-name`
   - Documentation: `docs/doc-name`
2. **Pull Request Checklist**:
   - [ ] Automated tests run locally and pass successfully.
   - [ ] Backend test statement coverage is above 85% (`pytest --cov`).
   - [ ] Security headers and rate limiting are applied where appropriate.
   - [ ] Accessibility: interactive elements are focusable, semantic HTML headings are correct, contrast values meet WCAG AA.
   - [ ] No hardcoded passwords, tokens, or configuration values are committed.

## Testing Guidelines

- **Unit Tests**: Place in `tests/` directories. Use `pytest` for Python and `vitest` for JavaScript.
- **Parametrized Boundaries**: Always write test cases covering upper/lower limit boundaries (e.g. density calculation margins).
- **Property-Based Testing**: Use `Hypothesis` to test invariants over broad ranges of generated values.
- **Atomicity & Fail-Safety**: Ensure multi-step actions (like PA broadcast updates or incident resolutions) rollback cleanly on mid-workflow failure.
