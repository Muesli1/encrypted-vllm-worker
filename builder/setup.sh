#!/bin/bash

set -e # Stop script on error
apt-get update && apt-get upgrade -y # Update System

# TODO: Download model via hf_transfer

# Clean up, remove unnecessary packages and help reduce image size
apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*
