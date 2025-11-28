# Docker Deployment

Run TAD in Docker containers for easy deployment and isolation.

## Quick Start

### Pull and Run

```bash
docker run -d \
  --name tad \
  --network host \
  -v tad-data:/app/data \
  fabriziosalmi/tad:latest
```

### Build from Source

```bash
git clone https://github.com/fabriziosalmi/tad.git
cd tad
docker build -t tad:local .
docker run -d --name tad --network host tad:local
```

## Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    avahi-daemon \
    avahi-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY tad/ ./tad/

# Create data directories
RUN mkdir -p /app/data /app/exports

# Set environment variables
ENV TAD_DATA_DIR=/app/data \
    TAD_EXPORT_DIR=/app/exports \
    PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8765/udp 8765/tcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.socket(); s.connect(('localhost', 8765)); s.close()"

# Run TAD
CMD ["python", "-m", "tad.main"]
```

## Docker Compose

### Basic Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tad:
    build: .
    container_name: tad
    restart: unless-stopped
    network_mode: host
    volumes:
      - tad-data:/app/data
      - tad-exports:/app/exports
    environment:
      - TAD_PORT=8765
      - TAD_LOG_LEVEL=INFO
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  tad-data:
  tad-exports:
```

### Multi-Node Setup

Run multiple TAD nodes:

```yaml
version: '3.8'

services:
  tad-node1:
    build: .
    container_name: tad-node1
    hostname: tad-node1
    network_mode: host
    volumes:
      - tad-node1-data:/app/data
    environment:
      - TAD_PORT=8765
      - TAD_NODE_NAME=node1

  tad-node2:
    build: .
    container_name: tad-node2
    hostname: tad-node2
    network_mode: host
    volumes:
      - tad-node2-data:/app/data
    environment:
      - TAD_PORT=8766
      - TAD_NODE_NAME=node2

  tad-node3:
    build: .
    container_name: tad-node3
    hostname: tad-node3
    network_mode: host
    volumes:
      - tad-node3-data:/app/data
    environment:
      - TAD_PORT=8767
      - TAD_NODE_NAME=node3

volumes:
  tad-node1-data:
  tad-node2-data:
  tad-node3-data:
```

## Docker Commands

### Build

```bash
# Build image
docker build -t tad:latest .

# Build with custom tag
docker build -t tad:v1.0 .

# Build with no cache
docker build --no-cache -t tad:latest .
```

### Run

```bash
# Run detached
docker run -d --name tad --network host tad:latest

# Run with custom port
docker run -d --name tad -e TAD_PORT=9000 --network host tad:latest

# Run with volume mounts
docker run -d --name tad \
  --network host \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/exports:/app/exports \
  tad:latest

# Run interactively
docker run -it --name tad --network host tad:latest
```

### Manage

```bash
# Start container
docker start tad

# Stop container
docker stop tad

# Restart container
docker restart tad

# View logs
docker logs tad
docker logs -f tad  # Follow logs

# Execute command in container
docker exec -it tad /bin/bash

# Inspect container
docker inspect tad

# Remove container
docker rm -f tad
```

### Docker Compose Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Scale services
docker-compose up -d --scale tad=3

# Build and start
docker-compose up -d --build
```

## Networking

### Host Network Mode (Recommended)

Best for mDNS/service discovery:

```yaml
services:
  tad:
    network_mode: host
```

Pros:
- ✅ mDNS works properly
- ✅ No port mapping needed
- ✅ Best performance

Cons:
- ❌ Less isolation
- ❌ Port conflicts possible

### Bridge Network Mode

Better isolation but requires configuration:

```yaml
services:
  tad:
    networks:
      - tad-network
    ports:
      - "8765:8765/tcp"
      - "8765:8765/udp"
      - "5353:5353/udp"  # mDNS

networks:
  tad-network:
    driver: bridge
```

### Custom Network

For multi-node testing:

```yaml
networks:
  tad-internal:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  tad:
    networks:
      tad-internal:
        ipv4_address: 172.20.0.10
```

## Volumes and Data Persistence

### Named Volumes

```yaml
volumes:
  tad-data:
  tad-exports:
  tad-logs:

services:
  tad:
    volumes:
      - tad-data:/app/data
      - tad-exports:/app/exports
      - tad-logs:/app/logs
```

### Bind Mounts

```yaml
services:
  tad:
    volumes:
      - ./data:/app/data
      - ./exports:/app/exports
      - ./config:/app/config:ro  # Read-only
```

### Backup Volumes

```bash
# Backup volume to tar
docker run --rm \
  -v tad-data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/tad-backup.tar.gz -C /data .

# Restore from backup
docker run --rm \
  -v tad-data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/tad-backup.tar.gz -C /data
```

## Environment Variables

```yaml
environment:
  # Network
  - TAD_PORT=8765
  - TAD_HOST=0.0.0.0
  - TAD_DISCOVERY=true
  
  # Channels
  - TAD_AUTO_JOIN=general,dev
  - TAD_DEFAULT_CHANNEL=general
  
  # Logging
  - TAD_LOG_LEVEL=INFO
  - TAD_LOG_FILE=/app/logs/tad.log
  
  # Database
  - TAD_DATA_DIR=/app/data
  - TAD_DB_PATH=/app/data/tad.db
  
  # Security
  - TAD_ENABLE_ENCRYPTION=true
  - TAD_KEY_SIZE=256
```

## Multi-Architecture Builds

### buildx for ARM/AMD64

```bash
# Create builder
docker buildx create --name tad-builder --use

# Build multi-arch image
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t fabriziosalmi/tad:latest \
  --push \
  .
```

### Platform-Specific Builds

```bash
# Build for Raspberry Pi
docker buildx build \
  --platform linux/arm/v7 \
  -t tad:rpi \
  .

# Build for Apple Silicon
docker buildx build \
  --platform linux/arm64 \
  -t tad:arm64 \
  .
```

## Docker Hub

### Push to Registry

```bash
# Tag image
docker tag tad:latest fabriziosalmi/tad:latest
docker tag tad:latest fabriziosalmi/tad:v1.0

# Login
docker login

# Push
docker push fabriziosalmi/tad:latest
docker push fabriziosalmi/tad:v1.0
```

### Pull from Registry

```bash
# Pull latest
docker pull fabriziosalmi/tad:latest

# Pull specific version
docker pull fabriziosalmi/tad:v1.0

# Pull and run
docker run -d --name tad --network host fabriziosalmi/tad:latest
```

## Production Deployment

### Complete Setup

```yaml
version: '3.8'

services:
  tad:
    image: fabriziosalmi/tad:latest
    container_name: tad
    restart: unless-stopped
    network_mode: host
    
    volumes:
      - tad-data:/app/data
      - tad-exports:/app/exports
      - tad-logs:/app/logs
      - ./config.yaml:/app/config.yaml:ro
    
    environment:
      - TAD_CONFIG_FILE=/app/config.yaml
      - TAD_LOG_LEVEL=INFO
    
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
    
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('localhost',8765))"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 128M

volumes:
  tad-data:
    driver: local
  tad-exports:
    driver: local
  tad-logs:
    driver: local
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'          # Max 2 CPU cores
      memory: 512M          # Max 512MB RAM
    reservations:
      cpus: '0.5'          # Guaranteed 0.5 cores
      memory: 128M          # Guaranteed 128MB RAM
```

## Monitoring

### Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m tad.health_check
```

### Prometheus Metrics

Add to compose:

```yaml
services:
  tad:
    # ... existing config ...
    ports:
      - "9090:9090"  # Metrics port
    environment:
      - TAD_METRICS_ENABLED=true
      - TAD_METRICS_PORT=9090
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs tad

# Run interactively for debugging
docker run -it --rm --network host tad:latest /bin/bash

# Check container status
docker ps -a
```

### mDNS Not Working

Ensure host network mode:
```yaml
network_mode: host
```

Or expose mDNS port:
```yaml
ports:
  - "5353:5353/udp"
```

### Permission Issues

```dockerfile
# Add in Dockerfile
RUN useradd -m -u 1000 tad && \
    chown -R tad:tad /app

USER tad
```

### Logs Not Appearing

```bash
# Check logging driver
docker inspect tad | grep LogConfig

# View with specific driver
docker logs --details tad
```

## See Also

- [Deployment](/guide/deployment) - System-wide installation
- [Service](/guide/service) - Running as service
- [Raspberry Pi](/guide/raspberry-pi) - ARM deployment
