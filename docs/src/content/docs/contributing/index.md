---
title: Contributing
description: How to contribute to AssoCORE
---

Thank you for your interest in contributing to AssoCORE! This guide will help you get started.

## Ways to Contribute

- **Code Contributions** - Submit bug fixes or new features
- **Documentation** - Improve or expand documentation
- **Bug Reports** - Help us identify issues
- **Feature Requests** - Suggest new features
- **Community Support** - Help other users
- **Testing** - Test new features and report issues

## Getting Started

### 1. Set Up Your Development Environment

Follow our comprehensive [Development Setup Guide](./development-setup.md) to:

- Install required tools (Python, Docker, etc.)
- Clone and configure the repository
- Run the application locally
- Set up your IDE and debugging tools

### 2. Understand Our Code Standards

Read our [Code Guidelines](./code-guidelines.md) to learn:

- Python code style and conventions
- FastAPI best practices
- Testing requirements
- Git commit message format
- Code review expectations

### 3. Pick an Issue or Feature

- Browse [GitHub Issues](https://github.com/AssoCORE/AssoCORE/issues)
- Look for issues tagged `good first issue` for beginners
- Comment on an issue to claim it
- Ask questions if anything is unclear

### 4. Development Workflow

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/AssoCORE.git
cd AssoCORE

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run tests and linters
poetry run pytest
poetry run black .
poetry run ruff check .

# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Open a Pull Request on GitHub
```

## Contribution Guidelines

### Code Quality

All contributions must:

- Pass all existing tests
- Include tests for new features
- Follow our code style (Black, Ruff, mypy)
- Include type hints
- Have clear documentation

### Pull Request Process

1. **Create a clear PR description**
   - Explain what changes you made and why
   - Reference related issues
   - Include screenshots for UI changes

2. **Ensure CI passes**
   - All tests must pass
   - Code must meet quality standards
   - No merge conflicts

3. **Respond to reviews**
   - Address reviewer feedback
   - Ask questions if needed
   - Update your PR as requested

4. **Wait for approval**
   - At least one maintainer must approve
   - Automated checks must pass
   - Branch must be up to date

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```zsh
type(scope): description

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Code style changes (formatting)
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**

```zsh
feat(auth): add OAuth2 authentication
fix(api): resolve user creation validation error
docs(readme): update installation instructions
test(users): add tests for user service
```

## Testing Requirements

### Test Coverage

- Aim for >80% code coverage
- All new features must have tests
- Bug fixes should include regression tests

### Test Types

```bash
# Unit tests
poetry run pytest tests/unit/

# Integration tests
poetry run pytest tests/integration/

# E2E tests
poetry run pytest tests/e2e/

# With coverage
poetry run pytest --cov=app --cov-report=html
```

## Documentation

### Code Documentation

- All public functions must have docstrings
- Use Google-style docstrings
- Include examples for complex functions

### Project Documentation

- Update relevant docs in `/docs`
- Keep README.md current
- Document breaking changes

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information
- Unprofessional conduct

## Getting Help

### Questions?

- **Technical questions**: Open a GitHub Discussion
- **Bug reports**: Create a GitHub Issue
- **Security issues**: Email <security@assocore.org>
- **General chat**: Join our community

### Resources

- [Development Setup](./development-setup.md) - Complete dev environment guide
- [Code Guidelines](./code-guidelines.md) - Coding standards and best practices
- [Architecture Docs](../architecture/) - Understanding the codebase
- [API Reference](../reference/) - API documentation

## Recognition

Contributors will be:

- Listed in our contributors page
- Mentioned in release notes for significant contributions
- Invited to join our contributors team

Thank you for making AssoCORE better! 🎉
