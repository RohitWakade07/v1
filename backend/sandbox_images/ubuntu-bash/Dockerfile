FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash git openssl ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -u 1000 -m -s /bin/bash grader

WORKDIR /workspace
