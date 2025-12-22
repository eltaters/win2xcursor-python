
# Contributions

Contributions are always welcome! Before starting any work, please read the
following guidelines:

## Start with an Issue

1. Open a new issue describing the bug or feature request.
1. If you want to contribute a fix, leave a comment on the issue.
1. Feel free to ask questions!

## Development

- `uv`: Environment/dependency management
- `ruff`: Formatter/linter
- `pre-commit`: Automatic formatting/linting checks

To set up your environment:

```bash
uv venv
source .venv/bin/activate
uv sync
pre-commit install
```

### Code Style

Contributions should pass the following checks:

- Static type analysis: `mypy --strict ./src`
- Documentation: Use **Google-style docstrings**
- Unit tests: `pytest` (update unit tests as needed)

### Branches

The `main` branch should always be **stable**. Create feature branches for your
work (e.g., `feature/add-skip-broken-flag`, `bugfix/42-improper-scaling`,
`docs/update-readme`, etc.)

## License

See [LICENSE](./LICENSE).
