# Jenkins CI/CD Learning Project

A hands-on project to learn **Jenkins** by building a real CI/CD pipeline.
Jenkins runs in a container, and it builds, tests and deploys a small Flask app that also runs in a container.

> Start here, then read the full guide: **[docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md)**

## What happens

```
 You push code ──> GitHub ──> Jenkins (container)
                                 │
                  Checkout → Test → Build Image → Deploy → Smoke Test
                                                     │
                                          App container on http://localhost:5000
```

## Repo structure

```
.
├── app/                    # The Flask application
│   ├── app.py
│   ├── requirements.txt
│   └── requirements-dev.txt
├── tests/test_app.py       # Automated tests (pytest)
├── Dockerfile              # Multi-stage: test -> final app image
├── Jenkinsfile             # The pipeline as code
├── jenkins/
│   ├── Dockerfile          # Jenkins image + Docker CLI
│   └── plugins.txt         # Jenkins plugins installed automatically
├── docker-compose.yml      # Starts Jenkins
├── docs/LEARNING_GUIDE.md  # Step-by-step learning guide (what, why, how)
├── .dockerignore
└── .gitignore
```

## Quick start

Requirements: Docker Desktop (or Docker Engine + Compose) and Git.

```bash
# 1. Start Jenkins
docker compose up -d --build

# 2. Get the first admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 3. Open http://localhost:8080, install suggested plugins, create the admin user
# 4. Create a Pipeline job pointing to your GitHub repo (see the guide), click "Build Now"
# 5. Open http://localhost:5000
```

## Run the app without Jenkins (optional)

```bash
pip install -r app/requirements-dev.txt
PYTHONPATH=app python -m pytest tests     # run tests
docker build -t jenkins-demo-app . && docker run -p 5000:5000 jenkins-demo-app
```

## Security note

`docker-compose.yml` gives Jenkins access to the Docker socket and runs it as root. This is fine for **learning on your own laptop**, but not for production. The guide explains why.
