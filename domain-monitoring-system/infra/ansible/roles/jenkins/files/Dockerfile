FROM jenkins/jenkins:lts-jdk21

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        docker-cli \
        docker-buildx \
    && rm -rf /var/lib/apt/lists/*

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt

RUN jenkins-plugin-cli \
    --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY init.groovy \
    /usr/share/jenkins/ref/init.groovy.d/init.groovy

USER jenkins