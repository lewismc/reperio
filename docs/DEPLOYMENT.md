# Deployment Guide

This guide covers deploying Reperio in various environments.

## Production Deployment

### Using Docker

#### Build Docker Image

```bash
# Build backend image
docker build -t reperio:latest -f docker/Dockerfile .

# Build frontend
cd frontend
npm run build
cd ..
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  reperio-api:
    image: reperio:latest
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - HDFS_NAMENODE=namenode
      - HDFS_PORT=9000
    volumes:
      - ./data:/data
      - ~/.reperio:/root/.reperio
    command: reperio serve --host 0.0.0.0 --port 8000

  reperio-frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - reperio-api
```

Create `nginx.conf` for frontend:

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://reperio-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Run with Docker Compose

```bash
docker-compose up -d
```

### Using Kubernetes

Create Kubernetes manifests:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reperio
spec:
  replicas: 2
  selector:
    matchLabels:
      app: reperio
  template:
    metadata:
      labels:
        app: reperio
    spec:
      containers:
      - name: reperio
        image: reperio:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        - name: HDFS_NAMENODE
          valueFrom:
            configMapKeyRef:
              name: reperio-config
              key: hdfs_namenode
---
apiVersion: v1
kind: Service
metadata:
  name: reperio-service
spec:
  selector:
    app: reperio
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Apply:

```bash
kubectl apply -f deployment.yaml
```

### Systemd Service

For bare-metal deployment, create `/etc/systemd/system/reperio.service`:

```ini
[Unit]
Description=Reperio API Service
After=network.target

[Service]
Type=simple
User=reperio
WorkingDirectory=/opt/reperio
Environment="PATH=/opt/reperio/.venv/bin"
ExecStart=/opt/reperio/.venv/bin/python -m reperio.__main__ serve --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable reperio
sudo systemctl start reperio
```

## HDFS Integration

### Kerberos Authentication

For secure Hadoop clusters with Kerberos:

```bash
# Obtain Kerberos ticket
kinit username@REALM

# Set Hadoop configuration
export HADOOP_CONF_DIR=/etc/hadoop/conf

# Run Reperio
reperio serve
```

### Configure HDFS Access

Option 1: Environment variables

```bash
export HDFS_NAMENODE=namenode.example.com
export HDFS_PORT=9000
export HADOOP_CONF_DIR=/etc/hadoop/conf
```

Option 2: .env file

```bash
HDFS_NAMENODE=namenode.example.com
HDFS_PORT=9000
HADOOP_CONF_DIR=/etc/hadoop/conf
```

Option 3: Configuration file

Create `~/.reperio/config.yaml`:

```yaml
hdfs:
  namenode: namenode.example.com
  port: 9000
  hadoop_conf_dir: /etc/hadoop/conf
```

## Performance Optimization

### Large Datasets

For datasets with millions of nodes:

1. **Use sampling**: Load subset of data
   ```bash
   poetry run reperio load /data/crawldb --type crawldb --max-records 100000
   ```

2. **Enable caching**: Set in `.env`
   ```bash
   CACHE_ENABLED=true
   CACHE_DIR=/var/cache/reperio
   ```

3. **Increase memory**: For Docker
   ```yaml
   services:
     reperio-api:
       deploy:
         resources:
           limits:
             memory: 4G
   ```

### Database Backend

For persistent storage, integrate with PostgreSQL or Redis:

```python
# In future versions, add database support
DATABASE_URL=postgresql://user:pass@localhost/reperio
REDIS_URL=redis://localhost:6379/0
```

## Security

### Enable HTTPS

Use Nginx as reverse proxy with SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name reperio.example.com;

    ssl_certificate /etc/ssl/certs/reperio.crt;
    ssl_certificate_key /etc/ssl/private/reperio.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### API Authentication

To add authentication (future feature):

```python
# Add to .env
API_KEY=your-secret-api-key
AUTH_ENABLED=true
```

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/api/health

# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Logging

Configure logging in `.env`:

```bash
LOG_LEVEL=INFO
LOG_FILE=/var/log/reperio/api.log
```

### Metrics

Prometheus metrics endpoint (planned):

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'reperio'
    static_configs:
      - targets: ['localhost:8000']
```

## Backup and Recovery

### Export Graph Data

```bash
# Regular backups
poetry run reperio export /data/crawldb backup-$(date +%Y%m%d).json \
  --type crawldb --format json

# Compressed backup
poetry run reperio export /data/linkdb - --type linkdb --format json | \
  gzip > backup-$(date +%Y%m%d).json.gz
```

### Cache Management

```bash
# Clear cache
rm -rf ~/.reperio/cache/*

# Set cache size limit
export CACHE_MAX_SIZE=10G
```

## Troubleshooting

### Common Issues

1. **HDFS Connection Failed**
   - Check namenode hostname/port
   - Verify Kerberos ticket: `klist`
   - Test HDFS access: `hdfs dfs -ls /`

2. **Out of Memory**
   - Reduce max_records limit
   - Increase Docker/container memory
   - Enable graph sampling

3. **Slow Visualization**
   - Reduce max_nodes in frontend
   - Enable server-side clustering
   - Use graph sampling

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
poetry run reperio serve
```

### Performance Profiling

```python
# Add to API for profiling
import cProfile
cProfile.run('app.run()')
```
