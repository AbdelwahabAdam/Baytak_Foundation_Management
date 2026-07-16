## ansible plan

- update packages
- install git
- install docker
    - Set up Docker's apt repository
        - apt update
        - install dependencies (ca-certificates curl)
        - install (-m 0755 -d /etc/apt/keyrings)
        - curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        - chmod a+r /etc/apt/keyrings/docker.asc
        - add the repo:
        ```
        sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
        ```
            -  apt update


    - Install the Docker packages.
        -  sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    - start docker ( sudo systemctl start docker)


    - Verify status ( sudo systemctl status docker)