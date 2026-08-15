# Docker Swarm Deployment SOP
## Domain Monitoring System — 3-Node Cluster

## Architecture
```
        ┌─────────────────┐
        │   Load Balancer │
        │   (Nginx:80)    │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│Manager │  │Worker 1│  │Worker 2│
│10.0.0.1│  │10.0.0.2│  │10.0.0.3│
└────────┘  └────────┘  └────────┘
```

## Step 1: Build and Push

```bash
docker build -t domain-monitoring-system:latest .
docker tag domain-monitoring-system:latest repo.devops.poalim.bank/docker-local/domain-monitoring-system:latest
docker push repo.devops.poalim.bank/docker-local/domain-monitoring-system:latest
```

## Step 2: Init Swarm (Manager)

```bash
docker swarm init --advertise-addr 10.0.0.1
```

## Step 3: Join Workers

```bash
docker swarm join --token SWMTKN-1-xxx 10.0.0.1:2377
```

## Step 4: Deploy

```bash
docker stack deploy -c docker-compose.yml dms
```

## Quick Reference

| Action | Command |
|--------|---------|
| Deploy | `docker stack deploy -c docker-compose.yml dms` |
| List | `docker service ls` |
| Scale | `docker service scale dms_app=5` |
| Logs | `docker service logs dms_app` |
| Remove | `docker stack rm dms` |
