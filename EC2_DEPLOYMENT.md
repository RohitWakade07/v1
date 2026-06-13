# AWS EC2 Worker Deployment Guide

Because the grading worker relies on Docker volume mounts to share files with the sandboxes, **the Celery worker must run on the same physical machine as the Docker daemon**. 

We will keep your API, Postgres, and Redis on Railway, but move the Worker to a dedicated AWS EC2 instance.

## Step 1: Provision an EC2 Instance
1. Go to the AWS Console → **EC2** → **Launch Instance**.
2. **Name**: `grading-worker`
3. **AMI**: **Ubuntu Server 24.04 LTS** (or 22.04 LTS).
4. **Instance Type**: Select **t3.medium** or **t3.large** (Docker grading needs CPU and Memory. t2.micro free tier will likely crash).
5. **Key Pair**: Create a new key pair or use an existing one so you can SSH into the instance.
6. **Network Settings**:
   - Allow **SSH traffic from Anywhere** (Port 22) so you can connect.
7. Launch the instance!

## Step 2: SSH into your Instance
```bash
ssh -i "your-key.pem" ubuntu@<your-ec2-public-ip>
```

## Step 3: Install Docker & Git
Once logged in, run these commands to install Docker and clone your code:

```bash
# Update and install Docker
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin git

# Allow ubuntu user to run docker without sudo
sudo usermod -aG docker ubuntu
```

*(You must **log out and log back in** via SSH for the `usermod` group change to take effect!)*

## Step 4: Clone your Repository
```bash
git clone https://github.com/RohitWakade07/v1.git grading-platform
cd grading-platform/backend
```

## Step 5: Create a dedicated `docker-compose.worker.yml`
Create a new file called `docker-compose.worker.yml` inside the `backend` folder on the server:

```yaml
services:
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    container_name: grading_worker
    restart: unless-stopped
    env_file: .env
    volumes:
      # Mount the Docker socket so the worker can spin up sibling containers
      - /var/run/docker.sock:/var/run/docker.sock
      # Shared jobs directory
      - grader_jobs:/tmp/autograder_jobs

volumes:
  grader_jobs:
```

## Step 6: Create the `.env` file
Inside the `backend` folder on the server, create a `.env` file with the connection strings from your Railway deployment:

```env
SERVICE_TYPE=worker

# Grab these from your Railway Dashboard (API Variables)
DATABASE_URL_OVERRIDE=postgresql://postgres:...
REDIS_URL_OVERRIDE=redis://default:...
CELERY_BROKER_URL=redis://default:.../0
CELERY_RESULT_BACKEND=redis://default:.../1

# Your Kafka and Minio vars
KAFKA_BOOTSTRAP_SERVERS=...
MINIO_ENDPOINT=...
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
```

## Step 7: Launch the Worker
Finally, run the worker in the background:

```bash
docker compose -f docker-compose.worker.yml up -d --build
```

You can view the live worker logs anytime with:
```bash
docker logs -f grading_worker
```

## Step 8: Clean up Railway
1. Go to your Railway Dashboard.
2. Select the **Worker** service.
3. Click **Settings** → **Danger Zone** → **Delete Service**.
(We no longer need Railway trying to run the worker, since EC2 is handling it now).
