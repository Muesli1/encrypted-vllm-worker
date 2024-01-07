#!/bin/bash

set -e # Stop script on error
apt-get update && apt-get upgrade -y # Update System

# Download model via huggingface_hub snapshot_download
python3.11 -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='$(VLLM_MODEL_NAME)')"

# Clean up, remove unnecessary packages and help reduce image size
apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*
