# Use a Debian-based Python image
FROM python:3.10.12-slim

# Install necessary system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Set the working directory
WORKDIR /opt/code

# Copy application code and requirements
COPY ./code /opt/code/
COPY ./requirements.txt /opt/requirements.txt

# Install Python dependencies
RUN pip install -r /opt/requirements.txt