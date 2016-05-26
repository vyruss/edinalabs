FROM cityscope/cityscope-jupyterhub-base:latest

RUN /opt/conda/bin/pip install docker-py
RUN /opt/conda/bin/pip install git+https://github.com/jupyter/dockerspawner.git
RUN /opt/conda/bin/pip install git+https://github.com/rgamez/jhub_remote_user_authenticator

RUN mkdir /srv/cityscope
WORKDIR /srv/cityscope
ADD . /srv/cityscope
