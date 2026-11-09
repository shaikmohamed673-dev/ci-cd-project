# Jenkins CI/CD Learning Project (Linux)

A hands-on project to learn **Jenkins** by building a real CI/CD pipeline.
Designed to run on a **Linux host** with Docker Engine and the Docker Compose plugin. Jenkins runs in a Linux container, and it builds, tests and deploys a small Flask app in another Linux container.

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

Requirements:
- A Linux host (Ubuntu or Debian recommended)
- Docker Engine with the Docker Compose plugin
- Git
- Python 3 and `python3-venv` (only needed to run tests outside Docker)

Install Docker Engine and the Compose plugin by following the [official instructions for your Linux distribution](https://docs.docker.com/engine/install/). Make sure the Docker service is running and your user can access it. On systemd-based distributions, you can start it with:

```bash
sudo systemctl enable --now docker
```

```bash
# 1. Start Jenkins
sudo docker compose up -d --build

# 2. Get the first admin password
sudo docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 3. Open http://localhost:8080, install suggested plugins, create the admin user
# 4. Create a Pipeline job pointing to your GitHub repo (see the guide), click "Build Now"
# 5. Open http://localhost:5000
```

## Run the app without Jenkins (optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/requirements-dev.txt
PYTHONPATH=app python -m pytest tests      # run tests
docker build -t jenkins-demo-app .
docker run --rm -p 5000:5000 jenkins-demo-app
```

## Security note

`docker-compose.yml` gives Jenkins access to the host Docker socket and runs it as root. This effectively grants Jenkins root-level control of the Linux host. Use this only for learning on a machine you control, not in production. The guide explains why.
