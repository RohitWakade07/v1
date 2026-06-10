FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev bash git openssl ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pytest requests urllib3

RUN useradd -u 1000 -m -s /bin/bash grader

WORKDIR /workspace
