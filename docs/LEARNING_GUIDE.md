# Jenkins Learning Guide

This guide teaches you **what** each part is, **why** we use it, and **how** to deploy it.
Read it in order and do every step yourself.

---

## 1. What are we building?

A **CI/CD pipeline**.

- **CI (Continuous Integration):** every time code changes, automatically build and test it.
- **CD (Continuous Delivery/Deployment):** after tests pass, automatically deploy the new version.

Without CI/CD, a person must run tests, build, and deploy by hand every time. This is slow and mistakes happen. Jenkins does it automatically and the same way every time.

### Flow

```
Developer ──push──> GitHub repo
                       │
                       ▼
               Jenkins (in a container)
                       │
   1. Checkout   : download the code
   2. Test       : run pytest inside Docker build
   3. Build Image: create the app Docker image (tagged with build number)
   4. Deploy     : stop old container, start new container
   5. Smoke Test : call /health to prove it works
                       │
                       ▼
        App container -> http://localhost:5000
```

---

## 2. Tools used and WHY

| Tool | What it is | Why we use it here |
|------|------------|--------------------|
| **Git / GitHub** | Version control and online code hosting | Jenkins needs a place to get the code from. Also your portfolio. |
| **Jenkins** | Automation server | Runs the pipeline automatically. Most widely used CI/CD tool in companies. |
| **Jenkinsfile** | Pipeline written as code | Pipeline is stored in Git with the code, so it is versioned and reviewable ("Pipeline as Code"). |
| **Docker** | Container platform | App runs the same everywhere ("works on my machine" problem solved). |
| **Dockerfile (multi-stage)** | Recipe to build an image | One file builds a test image and a small final image. |
| **Docker Compose** | Runs containers from a YAML file | Starts Jenkins with one command and saves settings. |
| **Flask + Gunicorn** | Python web framework + production server | Small app to deploy. Gunicorn is the real server; Flask's built-in one is for development only. |
| **pytest** | Python testing tool | The "Test" stage needs real tests that can fail. |
| **Docker network (`cicd-net`)** | Private network for containers | Lets Jenkins reach the app container by name for the smoke test. |
| **Docker volume (`jenkins_home`)** | Persistent storage | Jenkins keeps jobs and settings after a restart. |

---

## 3. Prerequisites

1. Install **Docker Desktop** (Windows/Mac) or **Docker Engine + Compose plugin** (Linux).
2. Install **Git** and create a **GitHub** account.
3. Check everything works:

```bash
docker --version
docker compose version
git --version
```

---

## 4. Deploy step by step

### Step 1: Put the project on GitHub

```bash
cd jenkins-cicd-learning-project
git init
git add .
git commit -m "Initial commit: Jenkins CI/CD learning project"
git branch -M main
git remote add origin https://github.com/<your-username>/jenkins-cicd-learning-project.git
git push -u origin main
```

(Create the empty repo on GitHub first. Keep it **public** so Jenkins can clone without credentials.)

### Step 2: Start Jenkins in a container

```bash
docker compose up -d --build
docker compose logs -f jenkins      # wait until you see "Jenkins is fully up and running"
```

- `up -d`: start in background.
- `--build`: build the custom Jenkins image (Jenkins + Docker CLI + plugins).

### Step 3: Unlock Jenkins

```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Open **http://localhost:8080**, paste the password, choose **Install suggested plugins**, create your admin user.

### Step 4: Create the pipeline job

1. Click **New Item** -> name `demo-app-pipeline` -> choose **Pipeline** -> OK.
2. Under **Pipeline**, set **Definition** = `Pipeline script from SCM`.
3. **SCM** = `Git`, **Repository URL** = your GitHub repo URL.
4. **Branch Specifier** = `*/main`.
5. **Script Path** = `Jenkinsfile`.
6. Save.

### Step 5: Run it

Click **Build Now**. Open the build -> **Console Output** and watch each stage.
When all stages are green, open **http://localhost:5000**. You should see the build number on the page.

### Step 6: See CI in action

1. Edit the message in `app/app.py` (e.g. change "Hello from Jenkins CI/CD!").
2. `git add . && git commit -m "change message" && git push`
3. Click **Build Now** again. Refresh `localhost:5000`. The build number increased and the text changed.

### Step 7: Break it on purpose (very important for learning)

Change a test in `tests/test_app.py` so it fails, push, and build. The **Test** stage turns red and **Deploy never runs**. This is the main value of CI: bad code does not reach deployment.

### Step 8: Auto-build on every push (optional)

By default you click Build Now. To make it automatic, either:

- **Poll SCM:** in the job, enable *Poll SCM* with schedule `* * * * *` (checks every minute). Easy, works on a laptop.
- **GitHub webhook:** GitHub calls Jenkins on push. Needs Jenkins reachable from the internet (e.g. with ngrok), so try this later.

---

## 5. The Jenkinsfile explained

| Part | Meaning |
|------|---------|
| `pipeline { }` | Declarative pipeline: a fixed, easy structure. |
| `agent any` | Run on any available Jenkins node. Later you can use dedicated agents. |
| `options { }` | Settings: timestamps in logs, 15 min timeout, keep last 10 builds. |
| `environment { }` | Variables used in all stages. |
| `stages { stage(...) }` | Ordered steps. If one fails, the next ones are skipped. |
| `checkout scm` | Downloads the repo that triggered the job. |
| `sh '...'` | Runs a shell command. |
| `${BUILD_NUMBER}` | Built-in Jenkins variable. We use it to tag images, so every build is traceable and can be rolled back. |
| `post { success / failure / always }` | Actions after stages finish. We print logs on failure and clean old images always. |

### Why each stage exists

1. **Checkout**: pipeline must test the exact code from Git.
2. **Test**: catch bugs early, before anything is deployed.
3. **Build Image**: package the app + dependencies into an immutable image.
4. **Deploy**: replace the old container with the new version.
5. **Smoke Test**: "container started" is not the same as "app works". We call `/health` to be sure.

---

## 6. The Dockerfile explained (multi-stage build)

```
base  ──> test   (adds pytest + tests, runs them)
  └─────> final  (small, runs as non-root user, has HEALTHCHECK)
```

- **Why multi-stage?** Test tools are not needed in production. The final image stays small and safer.
- **Why tests inside the build?** If tests fail, `docker build` fails, so the pipeline stops. No extra tool needed.
- **Why `USER appuser`?** Never run apps as root inside containers (security best practice).
- **Why `HEALTHCHECK`?** Docker can mark the container `healthy` or `unhealthy`. Check with `docker ps`.
- **Why copy `requirements.txt` first?** Docker caches layers. Dependencies are re-installed only when requirements change, so builds are faster.
- **`ARG BUILD_NUMBER`** is passed by Jenkins and shown in the app, so you can see which build is running.

---

## 7. docker-compose.yml explained

| Line | Why |
|------|-----|
| `build: ./jenkins` | Builds our custom Jenkins image. |
| `ports 8080:8080` | Opens the Jenkins web UI on your computer. |
| `jenkins_home` volume | Data survives `docker compose down`. |
| `/var/run/docker.sock` mount | Lets Jenkins use the **host's** Docker, so containers it starts appear next to Jenkins (sometimes called "Docker outside of Docker"). |
| `user: root` | Needed to access the socket easily in this learning setup. |
| `networks: cicd-net` | Jenkins and the app share a network so `curl http://jenkins-demo-app:5000` works. |

**Security warning:** access to the Docker socket is almost the same as root on the host. In real companies, builds run on separate agents or use safer tools (Kaniko, Podman, rootless Docker).

---

## 8. Jenkins concepts glossary

| Term | Simple meaning |
|------|----------------|
| **Job / Project** | One thing Jenkins runs (here: our pipeline). |
| **Build** | One run of a job. Has a number (#1, #2...). |
| **Pipeline** | A job defined as stages in code. |
| **Stage / Step** | A stage is a phase; steps are commands inside it. |
| **Agent / Node** | The machine that runs the build. |
| **Workspace** | Folder where Jenkins downloads code for a build. |
| **Plugin** | Add-on that gives Jenkins new features (Git, timestamps...). |
| **Credentials** | Safe storage for passwords, tokens, SSH keys. Never write secrets in the Jenkinsfile. |
| **Trigger** | What starts a build (manual, poll, webhook, schedule). |
| **Artifact** | A file produced by a build that you keep. |
| **Jenkins home** | Folder with all config and job data (our volume). |

---

## 9. Useful commands

```bash
docker ps                               # running containers
docker logs jenkins-demo-app            # app logs
docker logs -f jenkins                  # Jenkins logs
docker images                           # images (see tags per build number)
docker exec -it jenkins bash            # go inside Jenkins container
docker compose down                     # stop Jenkins (data kept)
docker compose down -v                  # stop and DELETE all Jenkins data
docker rm -f jenkins-demo-app           # remove the app container
```

Rollback example: run an older build
```bash
docker rm -f jenkins-demo-app
docker run -d --name jenkins-demo-app --network cicd-net -p 5000:5000 jenkins-demo-app:3
```

---

## 10. Troubleshooting

| Problem | Cause / Fix |
|---------|-------------|
| `docker: not found` in the build | Jenkins image was not built with Docker CLI. Run `docker compose up -d --build`. |
| `permission denied ... docker.sock` | Make sure `user: root` is in compose and the socket is mounted. On Linux check the socket path. |
| `port is already allocated` (5000 or 8080) | Another program uses it. Stop it or change the left side of the port mapping, e.g. `5001:5000`. |
| Smoke test cannot resolve `jenkins-demo-app` | Jenkins and the app must be on `cicd-net`. Check with `docker network inspect cicd-net`. |
| Cannot clone repo | Repo is private. Add credentials in Jenkins (Manage Jenkins -> Credentials) and select them in the job. |
| Plugins fail to download | Check internet; restart with `docker compose restart jenkins`. |
| Build is slow the first time | Docker is downloading base images. Later builds use the cache. |

---

## 11. Practice exercises (to really learn)

1. Add a new endpoint `/api/time` and a test for it. Push and watch the pipeline.
2. Make a test fail and see the pipeline stop at **Test**.
3. Add a **Lint** stage (flake8) before Test.
4. Add a `parameters { string(name: 'APP_PORT', defaultValue: '5000') }` block to the pipeline.
5. Add a `triggers { pollSCM('H/2 * * * *') }` block.
6. Store a fake secret in Jenkins Credentials and use it with `withCredentials`.
7. Push the image to Docker Hub with a **Push** stage.
8. Add a `Jenkinsfile` stage that sends a notification (email or Slack plugin).
9. Run the pipeline on a **separate agent** container.
10. Deploy to a cloud VM (AWS EC2) using SSH instead of local Docker.

---

## 12. Common interview questions this project prepares you for

1. What is CI/CD and why is it used?
2. What is the difference between Continuous Delivery and Continuous Deployment?
3. What is a Jenkinsfile? Declarative vs Scripted pipeline?
4. What is the difference between a Docker image and a container?
5. What is a multi-stage Docker build?
6. How do you keep secrets safe in Jenkins?
7. How do you roll back a bad deployment? (Answer: image tags by build number.)
8. What is a smoke test?
9. Why is mounting `docker.sock` risky?
10. How do you trigger Jenkins automatically from Git?

---

## 13. Where to go next

- Push images to **Docker Hub / AWS ECR**.
- Deploy to **AWS EC2** or **Kubernetes** (Minikube first).
- Use **Terraform** to create the server, then Jenkins to deploy to it.
- Add **security scanning** (Trivy) to the pipeline.
- Add **Jenkins Configuration as Code (JCasC)** so Jenkins itself is set up from a file.
- Learn **GitHub Actions** and compare it with Jenkins.
