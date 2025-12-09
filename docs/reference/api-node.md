# TADNode API

> [!WARNING]
> This documentation is currently being updated.

The `TADNode` class is the core component of the system.

## Class: TADNode

```python
class TADNode:
    """
    Main node class for the TAD p2p chat system.
    Handles discovery, connections, gossip, and message routing.
    """
```

### Methods

#### start()
Starts the node, enabling discovery and network listeners.

#### stop()
Stops the node and closes all connections.
