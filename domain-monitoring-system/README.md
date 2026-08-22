# Domain Monitoring System

A Flask application for monitoring domain availability and SSL certificate information. The project began as a monolith and was later split into two independently containerized services:

- **Frontend** — owns the web interface, browser session and communication with the backend.
- **Backend** — owns authentication, domain storage, monitoring and scheduled scans.

The project demonstrates Docker networking, external configuration, containerized Selenium testing and a Jenkins pipeline running on a Docker agent.

## Architecture

```text
Browser
   |
   v
Frontend service :5000
   |
   | HTTP/JSON through backend_client.py
   v
Backend service :5001
   |
   +-- Authentication service
   +-- Domain service
   +-- Monitoring service
   +-- APScheduler
   |
   v
JSON file storage
```

Only the frontend is published to the host. The backend remains inside the Docker network and is reached by its service name:

```text
http://backend:5001
```

## Features

- User registration, login and frontend session handling
- Add, remove and bulk-upload domains
- Concurrent domain availability checks
- SSL expiration and issuer collection
- Scan one domain or all domains
- Interval and daily scheduled scans
- External JSON configuration
- Separate frontend and backend Docker images
- Headless Selenium tests in a dedicated container
- Jenkins stages for checkout, build, run, test and cleanup

## Technology

- Python 3.11
- Flask
- Requests
- APScheduler
- HTML, CSS and JavaScript
- Docker and Docker Compose
- Selenium and pytest
- Jenkins Declarative Pipeline

## Project structure

```text
domain-monitoring-system/
|-- backend/
|   |-- app.py
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- services/
|   |   |-- auth_service.py
|   |   |-- domain_service.py
|   |   |-- monitoring_service.py
|   |   `-- utils.py
|   `-- data/                  # Runtime JSON files; ignored by Git
|-- frontend/
|   |-- app.py
|   |-- backend_client.py
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- templates/
|   `-- static/
|-- tests/
|   |-- Dockerfile.selenium
|   |-- requirements-selenium.txt
|   `-- test_selenium.py
|-- Jenkins/
|   `-- Jenkinsfile.ci
|-- Docs/
|-- config.json
|-- settings.py
|-- docker-compose.yml
|-- .dockerignore
`-- .gitignore
```

## Configuration

Non-secret settings are stored in `config.json` and loaded by `settings.py`.

| Variable | Service | Purpose |
|---|---|---|
| `SECRET_KEY` | Frontend | Signs the Flask session cookie; required at startup |
| `BACKEND_URL` | Frontend | Overrides the configured backend address |
| `APP_CONFIG_FILE` | Both | Optional path to another JSON configuration file |
| `BASE_URL` | Selenium | Overrides the UI address used by Selenium |

Secrets are supplied at runtime and are not stored in the Dockerfiles or `config.json`.

## Run locally without Docker

Use two PowerShell terminals from the project directory.

Install the dependencies:

```powershell
python -m pip install -r backend/requirements.txt
python -m pip install -r frontend/requirements.txt
```

Start the backend in the first terminal:

```powershell
python -m backend.app
```

Start the frontend in the second terminal:

```powershell
$env:SECRET_KEY = "local-development-secret"
$env:BACKEND_URL = "http://127.0.0.1:5001"
python -m frontend.app
```

Open `http://127.0.0.1:5000`.

## Run with Docker Compose

```powershell
$env:SECRET_KEY = "local-compose-secret"
docker compose up -d --build
docker compose ps
```

Open `http://127.0.0.1:5000`.

View logs:

```powershell
docker compose logs -f
```

Stop the services without deleting application data:

```powershell
docker compose down
```

The backend JSON data is mounted from `./backend/data` and is ignored by Git and Docker builds.

## Build the images separately

```powershell
docker build -f backend/Dockerfile -t dms-backend:test .
docker build -f frontend/Dockerfile -t dms-frontend:test .
docker build -f tests/Dockerfile.selenium -t dms-selenium:test .
```

## Health checks

Frontend health check from the host:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Backend health check from its container:

```powershell
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5001/health').read().decode())"
```

Expected responses identify the service and return a `healthy` status.

## Selenium tests

The tests run in headless Chromium inside a dedicated image. In Jenkins, the frontend receives the network alias `monitoring-app`, matching the default Selenium URL in `config.json`.

For a local Compose run:

```powershell
$env:SECRET_KEY = "local-compose-secret"
docker compose up -d --build
docker build -f tests/Dockerfile.selenium -t dms-selenium:test .
docker run --rm --network domain-monitoring-system_dms-network -e BASE_URL=http://frontend:5000 dms-selenium:test
```

The suite covers registration, login, validation, domain management and the health endpoint.

## Jenkins pipeline

The CI pipeline is defined in `Jenkins/Jenkinsfile.ci`. When Jenkins checks out the parent repository, use this Script Path:

```text
domain-monitoring-system/Jenkins/Jenkinsfile.ci
```

Jenkins agent requirements:

- Node label: `docker`
- Docker CLI access
- Git
- Jenkins secret-text credential ID: `dms-secret-key`
- Pipeline and Stage View plugins

Pipeline flow:

```text
Clean Workspace
    -> Git Clone
    -> Build backend, frontend and Selenium images
    -> Create an isolated CI network
    -> Run and health-check the backend
    -> Run and health-check the frontend
    -> Run headless Selenium tests
    -> Print logs and remove CI resources
```

The backend uses the network alias `backend`. The frontend uses `monitoring-app`, allowing Selenium to reach it without publishing a host port.

## API overview

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a user |
| `POST` | `/api/v1/auth/login` | Validate credentials |
| `GET` | `/api/v1/domains` | List domains |
| `POST` | `/api/v1/domains` | Add a domain |
| `DELETE` | `/api/v1/domains/<domain>` | Remove a domain |
| `DELETE` | `/api/v1/domains` | Remove all domains |
| `POST` | `/api/v1/domains/bulk` | Add multiple domains |
| `POST` | `/api/v1/scan` | Scan all domains |
| `POST` | `/api/v1/scan/<domain>` | Scan one domain |
| `POST` | `/api/v1/schedule/start` | Start scheduled scans |
| `POST` | `/api/v1/schedule/stop` | Stop scheduled scans |
| `GET` | `/api/v1/schedule/status` | Read scheduler status |

## Docker Swarm

The earlier Docker Swarm deployment and operational notes are documented in:

- [SWARM-SOP.md](SWARM-SOP.md)
- [Jenkins and Docker Swarm exercise](Docs/Jenkins-Docker-Swarm-Exercise.md)

The current CI pipeline validates both microservices on one Jenkins Docker agent. A future deployment pipeline can publish the two images and deploy them as separate Swarm services.

## Known limitations and future improvements

This is an educational portfolio project. Before production use:

- Passwords must be hashed instead of stored directly in JSON.
- JSON file storage should be replaced by a database.
- Backend API authentication should use signed tokens or another service-authentication mechanism.
- Scheduled jobs should use persistent storage.
- The Flask development server should be replaced by a production WSGI server.
- Unit and API tests should be rebuilt for the two-service architecture.
- The two images still need versioned Docker Hub publication and Swarm deployment configuration.

## Documentation

- [Jenkins and Docker Swarm exercise](Docs/Jenkins-Docker-Swarm-Exercise.md)
- [Swarm operating procedure](SWARM-SOP.md)
- [Test results summary](TEST_RESULTS_SUMMARY.md)
- [Product requirements](Docs/Product%20Requirements%20Document%20(PRD))
- [High-level design](Docs/High-Level%20Design%20(HLD))
- [Low-level design](Docs/Low-Level%20Design%20(LLD))

## License

Educational portfolio project, August 2026.
