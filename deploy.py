import os
import subprocess

# Read registry image from environment variable (no hardcoded secrets)
IMAGE = os.getenv("DEPLOY_IMAGE", "ghcr.io/malek-hnaien/devops-demo:latest")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "devops-app")

# If run via `pyinfra @local deploy.py`, use pyinfra's server.shell
try:
    from pyinfra.operations import server
    server.shell(
        name="Pull latest image from registry",
        commands=[f"docker pull {IMAGE}"],
    )
    server.shell(
        name="Stop and remove existing container (idempotent)",
        commands=[
            f"docker stop {CONTAINER_NAME} || true",
            f"docker rm {CONTAINER_NAME} || true",
        ],
    )
    server.shell(
        name="Start updated container",
        commands=[
            f"docker run -d --name {CONTAINER_NAME} -p 3000:3000 --restart unless-stopped {IMAGE}"
        ],
    )
except ImportError:
    pass

def deploy_local():
    print(f"1. Pulling latest image: {IMAGE}...")
    subprocess.run(["docker", "pull", IMAGE], check=True)

    print("2. Stopping old container (idempotent)...")
    subprocess.run(["docker-compose", "down"], check=False)
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], check=False)

    print("3. Starting updated application stack...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    print("Deployment complete! Checking /health -> http://localhost:3000/health")

if __name__ == "__main__":
    deploy_local()