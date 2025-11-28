# Contributing to TAD

Thank you for your interest in contributing to TAD! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your changes
5. Make your changes
6. Run the test suite
7. Submit a pull request

## Development Environment

### Prerequisites

- Python 3.8 or higher
- Git
- pip and venv

### Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/tad.git
cd tad

# Add upstream remote
git remote add upstream https://github.com/fabriziosalmi/tad.git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-asyncio black flake8 mypy
```

### Verify Installation

```bash
# Run test suite
pytest tests/ -v

# Expected output: 97/97 tests passing
```

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_node.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=tad --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run Integration Tests

```bash
pytest tests/test_integration.py -v
```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Maximum line length: 100 characters

### Format Code

```bash
# Format with Black
black tad/ tests/

# Check with flake8
flake8 tad/ tests/ --max-line-length=100

# Type check with mypy
mypy tad/
```

### Docstring Format

Use Google-style docstrings:

```python
def send_message(channel: str, content: str) -> bool:
    """Send a message to a specific channel.

    Args:
        channel: The channel identifier (e.g., "#general")
        content: The message content to send

    Returns:
        True if message was sent successfully, False otherwise

    Raises:
        ValueError: If channel name is invalid
    """
    pass
```

## Commit Messages

### Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): subject

body

footer
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

### Examples

```
feat(crypto): add AES-256-GCM encryption for private channels

Implements end-to-end encryption using AES-256-GCM with X25519 key exchange.
Private channels now encrypt all message content before transmission.

Closes #42
```

```
fix(discovery): handle mDNS timeout on slow networks

Added retry logic with exponential backoff for mDNS service registration.
Fixes connection issues on congested networks.

Fixes #87
```

## Pull Request Process

### Before Submitting

1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run the full test suite** and ensure all tests pass:
   ```bash
   pytest tests/ -v
   ```

3. **Check code style**:
   ```bash
   black tad/ tests/
   flake8 tad/ tests/ --max-line-length=100
   ```

4. **Update documentation** if you changed functionality:
   - Update relevant `.md` files
   - Update docstrings
   - Add examples if applicable

### Submitting

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Reference related issues (e.g., "Fixes #123")
   - Describe what changed and why
   - Include test results if applicable

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Related Issues
Fixes #123
Related to #456

## Changes
- Added X feature
- Fixed Y bug
- Refactored Z module

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Manual testing performed

## Documentation
- [ ] Updated relevant documentation
- [ ] Added docstrings to new functions
- [ ] Updated CHANGELOG.md
```

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR

## Reporting Bugs

### Before Reporting

1. **Check existing issues** to avoid duplicates
2. **Verify the bug** on the latest version
3. **Collect relevant information**:
   - Operating system and version
   - Python version
   - TAD version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs

### Bug Report Template

```markdown
**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10.5]
- TAD: [e.g., v1.0]

**Description:**
Clear and concise description of the bug.

**Steps to Reproduce:**
1. Start TAD with `python -m tad.main`
2. Run command `/create #test`
3. Observe error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Logs:**
```
Paste relevant error messages or logs here
```

**Additional Context:**
Any other relevant information.
```

## Suggesting Features

### Feature Request Template

```markdown
**Problem:**
Describe the problem or limitation you're trying to solve.

**Proposed Solution:**
Describe your proposed solution in detail.

**Alternatives Considered:**
What other solutions did you consider?

**Use Case:**
Describe a specific scenario where this feature would be useful.

**Additional Context:**
Any other relevant information, mockups, or examples.
```

## Development Workflow

### Working on a Feature

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/awesome-feature

# Make changes
# ... edit files ...

# Run tests frequently
pytest tests/ -v

# Commit changes
git add .
git commit -m "feat: add awesome feature"

# Push to your fork
git push origin feature/awesome-feature

# Open PR on GitHub
```

### Working on a Bug Fix

```bash
# Create bug fix branch
git checkout -b fix/issue-123

# Fix the bug
# ... edit files ...

# Add test that reproduces the bug
# ... edit tests/test_*.py ...

# Verify fix
pytest tests/ -v

# Commit
git commit -m "fix: resolve issue with X

Fixes #123"

# Push and PR
git push origin fix/issue-123
```

## Project Structure

```
tad/
├── tad/                    # Main package
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── node.py            # Core node logic
│   ├── identity.py        # Identity management
│   ├── crypto/            # Cryptography
│   ├── network/           # Networking
│   ├── persistence/       # Database
│   └── ui/                # Terminal UI
├── tests/                 # Test suite
│   ├── test_node.py
│   ├── test_gossip.py
│   ├── test_integration.py
│   └── conftest.py
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
└── README.md
```

## Questions?

- Open a [GitHub Discussion](https://github.com/fabriziosalmi/tad/discussions)
- Open an [Issue](https://github.com/fabriziosalmi/tad/issues) for bugs or feature requests
- Check the [User Guide](USER_GUIDE.md) for usage questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
