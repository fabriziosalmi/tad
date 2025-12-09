# Testing Guide

TAD maintains a comprehensive test suite with high code coverage. This guide explains how to run tests and verify your changes.

## Prerequisites

Ensure you have the development dependencies installed:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio
```

## Running Tests

### Run All Tests

To run the entire test suite:

```bash
pytest tests/ -v
```

Expected output: `97 passed` (or more).

### Run Specific Test Files

You can run individual test files to focus on specific functionality:

```bash
# Node functionality
pytest tests/test_node.py -v

# Integration tests
pytest tests/test_integration.py -v

# Gossip protocol
pytest tests/test_gossip.py -v
```

### Running with Coverage

To generate a coverage report:

```bash
pytest tests/ --cov=tad --cov-report=html
```

This will create an `htmlcov` directory. Open `htmlcov/index.html` in your browser to view the detailed line-by-line coverage report.

## Test Structure

- `tests/test_node.py`: Unit tests for the core `TADNode` class.
- `tests/test_gossip.py`: Tests for the gossip protocol and message propagation.
- `tests/test_integration.py`: Integration tests involving multiple nodes.
- `tests/test_milestone*.py`: Tests specific to development milestones (persistence, channels, TUI).
- `tests/conftest.py`: Shared pytest fixtures and configuration.

## Writing Tests

When adding new features, please include corresponding tests. We use `pytest-asyncio` for asynchronous testing.

Example test structure:

```python
import pytest
from tad.node import TADNode

@pytest.mark.asyncio
async def test_new_feature():
    node = TADNode()
    await node.start()
    # ... assert behavior ...
    await node.stop()
```
