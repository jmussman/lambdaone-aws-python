# See here for image contents: https://github.com/devcontainers/images/blob/22ce794a06cb34e12674d6aaf5e4549f6ab8ee4e/src/javascript-node/.devcontainer/Dockerfile

# [Choice] Node.js version: 18, 20
# ARG VARIANT="latest"
ARG VARIANT="3.12"
FROM mcr.microsoft.com/devcontainers/python:${VARIENT}

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive

# Pick up any other needed packages.

RUN curl -L -o /tmp/gh.deb https://github.com/cli/cli/releases/download/v2.53.0/gh_2.53.0_linux_amd64.deb
RUN apt install -y /tmp/gh.deb