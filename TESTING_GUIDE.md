# TAZCOM Testing Guide

## Overview

The TAZCOM project includes a comprehensive test suite covering:

- **Unit Tests** for TAZCOMNode backend logic
- **Integration Tests** for the full TAZCOMChatApp application
- **Fixture-based Testing** with reusable mocks and utilities

All tests use `pytest` with `pytest-asyncio` for async support.

---

## Setup

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest>=7.0.0` - Test runner
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-mock>=3.10.0` - Enhanced mocking utilities

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_node.py      # Unit tests only
pytest tests/test_integration.py # Integration tests only
```

### Run Specific Test Class

```bash
pytest tests/test_node.py::TestIdentityManagement
pytest tests/test_node.py::TestPeerManagement
```

### Run Specific Test

```bash
pytest tests/test_node.py::TestIdentityManagement::test_identity_creation_and_persistence
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
# View coverage in htmlcov/index.html
```

### Run with Custom Timeout

```bash
pytest --timeout=60  # 60 second timeout per test
```

---

## Test Structure

### tests/conftest.py

Provides shared fixtures used across all tests:

| Fixture | Purpose |
|---------|---------|
| `mock_app` | Mock TAZCOMChatApp for unit testing |
| `temp_node_dir` | Temporary directory for node.key files |
| `initialized_node` | TAZCOMNode with initialized identity |
| `mock_stream_reader` | Mock asyncio.StreamReader |
| `mock_stream_writer` | Mock asyncio.StreamWriter |
| `mock_zeroconf_service_info` | Mock Zeroconf ServiceInfo |
| `chat_message` | Sample CHAT message dict |
| `hello_message` | Sample HELLO message dict |

### tests/test_node.py

Unit tests for TAZCOMNode backend:

**TestIdentityManagement**
- `test_identity_creation_and_persistence` - Ed25519 key generation and persistence
- `test_identity_format` - node_id_b64 format validation
- `test_identity_uniqueness` - Each node gets unique identity

**TestPeerManagement**
- `test_on_service_added` - Peer discovery via Zeroconf
- `test_on_service_added_ignores_self` - Node ignores its own service
- `test_on_service_removed` - Peer removal and cleanup
- `test_on_service_removed_nonexistent_peer` - Graceful handling

**TestMessageHandling**
- `test_handle_hello_message` - HELLO message reception
- `test_handle_chat_message` - CHAT message reception
- `test_handle_invalid_json` - Invalid JSON error handling
- `test_handle_message_too_large` - Oversized message handling

**TestBroadcastMessage**
- `test_broadcast_with_no_peers` - Broadcasting to empty peer list
- `test_broadcast_with_peers` - Broadcasting to active peers
- `test_broadcast_empty_message` - Handling empty messages

**TestThreadSafety**
- `test_peers_lock_prevents_race_condition` - Async lock correctness

**TestShutdown**
- `test_shutdown_with_no_server` - Graceful shutdown
- `test_shutdown_closes_server` - Server cleanup

### tests/test_integration.py

Integration tests for the full application:

**TestFullApplicationFlow**
- `test_app_initialization` - App can be created
- `test_peer_discovery_in_app` - Two apps discover each other
- `test_message_reception_callback` - Received messages handled
- `test_peer_list_update_callback` - Peer list updates work

**TestMessageFlow**
- `test_broadcast_message_flow` - Full message transmission

**TestErrorHandling**
- `test_app_handles_missing_node` - Graceful error handling
- `test_app_handles_empty_message` - Empty message handling

**TestUIWidgetUpdates**
- `test_peer_list_widget_updates` - Peer list widget updates
- `test_message_history_widget_display` - Message history widget

**TestConcurrentOperations**
- `test_concurrent_message_reception` - Multiple simultaneous messages
- `test_concurrent_peer_updates` - Rapid peer list changes

**TestCleanup**
- `test_app_shutdown_cleanup` - Resource cleanup on shutdown

---

## What Gets Tested

### Backend (TAZCOMNode)

✅ **Identity Management**
- Ed25519 key generation
- Key persistence to node.key
- Key loading on restart
- Unique identity per node

✅ **Peer Discovery**
- Zeroconf service registration
- Service discovery callbacks
- Peer list management
- O(1) peer removal via inverse lookup

✅ **Message Handling**
- HELLO message processing
- CHAT message processing
- JSON parsing
- Message size validation
- Error responses

✅ **Broadcasting**
- Message broadcast to all peers
- Handling empty peer list
- Concurrent sends

✅ **Thread Safety**
- asyncio.Lock for shared state
- No race conditions
- Safe concurrent access

✅ **Shutdown**
- Graceful server closure
- Zeroconf cleanup
- Resource deallocation

### Application (TAZCOMChatApp)

✅ **Initialization**
- App creation
- Node initialization
- Widget setup

✅ **Message Reception**
- Peer messages displayed
- Local messages tracked
- System messages shown

✅ **Peer Updates**
- Peer list refreshed
- New peers detected
- Peer removal handled

✅ **Concurrent Operations**
- Multiple simultaneous messages
- Rapid peer updates
- Non-blocking UI

✅ **Error Handling**
- Missing node handled
- Empty messages safe
- Network errors caught

---

## Test Isolation

Tests are isolated by:

1. **Temporary Directories** - Each test gets its own temp dir for node.key
2. **Mock Objects** - Zeroconf and TCP streams are mocked
3. **No Real Network** - Tests use mocks, not actual network I/O
4. **Fixture Cleanup** - Resources cleaned up after each test

This ensures:
- Tests don't interfere with each other
- Tests are repeatable and deterministic
- Tests run quickly (no real network delays)
- Tests can run in parallel

---

## Writing New Tests

### Example Unit Test

```python
@pytest.mark.asyncio
async def test_new_feature(initialized_node):
    """Test description."""
    node = initialized_node

    # Setup
    node.some_property = "value"

    # Act
    result = await node.some_method()

    # Assert
    assert result == expected_value
    node.app.some_callback.assert_called()
```

### Example Integration Test

```python
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_new_behavior(temp_node_dir):
    """Test description."""
    app = TAZCOMChatApp()

    # Setup
    app.node = MagicMock()
    app.node.some_property = "value"

    # Act
    app.some_method()

    # Assert
    app.node.some_method.assert_called()
```

### Common Fixtures to Use

```python
async def test_something(
    initialized_node,           # TAZCOMNode with mock app
    mock_app,                   # MagicMock of app
    mock_stream_reader,         # Mock TCP reader
    mock_stream_writer,         # Mock TCP writer
    mock_zeroconf_service_info, # Mock service
    chat_message,               # Sample CHAT dict
    hello_message,              # Sample HELLO dict
    temp_node_dir               # Temp directory
):
    pass
```

---

## Debugging Tests

### Print Debug Info

```python
def test_something():
    node = ...
    print(f"Node ID: {node.node_id_b64}")  # stdout captured by pytest
    # Run with: pytest -s
```

### Run Single Test with Debug

```bash
pytest -s -vv tests/test_node.py::TestIdentityManagement::test_identity_creation_and_persistence
```

### Use pdb

```python
def test_something():
    import pdb; pdb.set_trace()  # Breakpoint
    ...
```

Run with:
```bash
pytest --pdb
```

### Show Local Variables on Failure

```bash
pytest -l
```

---

## Expected Test Output

### Successful Run

```
tests/test_node.py::TestIdentityManagement::test_identity_creation_and_persistence PASSED [10%]
tests/test_node.py::TestIdentityManagement::test_identity_format PASSED                    [20%]
...
============================== 25 passed in 2.34s ===============================
```

### With Coverage

```
Name                      Stmts   Miss  Cover
---------------------------------------------
poc-03_chat_basic.py      450     45    90%
tests/conftest.py         120      5    96%
---------------------------------------------
TOTAL                     570     50    91%
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## Performance Notes

- **Unit Tests:** <100ms total (no network)
- **Integration Tests:** <5s each (mocked networking)
- **Full Suite:** ~10-15 seconds

Tests are fast because:
1. No real network I/O
2. No file system overhead (temp dirs)
3. Async support prevents blocking
4. Mocks avoid sleep/delays

---

## Troubleshooting

### Import Errors

If `from poc_03_chat_basic import ...` fails:

```bash
# Make sure you're in the project root
cd /path/to/fan

# Ensure PYTHONPATH includes current directory
export PYTHONPATH=.:$PYTHONPATH
pytest
```

### Asyncio Event Loop Issues

If you get "no running event loop" errors:

```python
# conftest.py already handles this, but if you need to debug:
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())
```

### Timeout Issues

Tests have 30-second timeout. If test hangs:

```bash
pytest --timeout=10 -s  # 10 second timeout, show output
```

### Mock Not Working

If mock isn't recording calls:

```python
# Make sure to use the fixture
def test_something(mock_app):  # Include fixture parameter
    mock_app.method.assert_called()
```

---

## Best Practices

✅ **Do:**
- Use fixtures for setup/teardown
- Name tests clearly (`test_what_is_being_tested`)
- Test one thing per test function
- Use `@pytest.mark.asyncio` for async tests
- Clean up resources (fixtures handle this)

❌ **Don't:**
- Make tests depend on each other
- Use real network I/O in tests
- Use global state
- Skip cleanup
- Create files outside temp directories

---

## Next Steps

After tests are passing:

1. **Add more tests** for new features
2. **Increase coverage** to >90%
3. **Set up CI/CD** to run tests on every push
4. **Monitor performance** with timing data
5. **Refactor based on test insights**

The test suite is your safety net for development!

---

## Summary

| Command | Purpose |
|---------|---------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output |
| `pytest -s` | Show print statements |
| `pytest --timeout=30` | 30-second timeout |
| `pytest --cov` | Coverage report |
| `pytest tests/test_node.py` | Run specific file |
| `pytest -k "identity"` | Run tests matching pattern |

**Status:** Test suite ready for development! 🎉
