#!/bin/sh

sudo curl -sSL https://get.docker.com/ | sh
sudo apt-get update && sudo apt-get upgrade

sudo groupadd docker

sudo usermod -aG docker $USER

sudo curl -L https://github.com/docker/compose/releases/download/1.21.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose