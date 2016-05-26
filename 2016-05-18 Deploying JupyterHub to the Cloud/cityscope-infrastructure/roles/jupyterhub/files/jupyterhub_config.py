# Configuration file for Jupyter Hub
import os

c = get_config()

NOTEBOOKS_DIR= '/data/'

# use the remote autheticator
c.JupyterHub.authenticator_class = 'remote_user.RemoteUserAuthenticator'
c.RemoteUserAuthenticator.header_name = 'X-Proxy-Remote-User'
c.Authenticator.admin_users = {'rgamez', 'bbutchar', 'rgood'}

c.JupyterHub.proxy_api_ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'

# spawn with Docker
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.remove_containers = False
c.DockerSpawner.container_image = "jupyter/singleuser"
c.DockerSpawner.notebook_dir = NOTEBOOKS_DIR
c.DockerSpawner.extra_host_config = {'publish_all_ports': True}
c.DockerSpawner.extra_create_kwargs = {
    'volume_driver': 'convoy'
}
c.DockerSpawner.volumes = {
    '{username}': '/data'
}
c.DockerSpawner.container_ip = '0.0.0.0'
c.DockerSpawner.hub_ip_connect = os.environ['HUB_IP']

# Data API config
c.JupyterHub.data_api_spawner_class = 'jupyterhub.data_api_spawner.DockerProcessSpawner'
c.DockerProcessSpawner.github_api_token = os.environ['GITHUB_TOKEN']
c.DockerProcessSpawner.notebook_base_dir = NOTEBOOKS_DIR
c.DockerProcessSpawner.container_image = 'cityscope/cityscope-loopback:latest'
c.DockerProcessSpawner.container_prefix = 'loopback'
c.DockerProcessSpawner.extra_host_config = {
    'publish_all_ports': True,
    'port_bindings': {
        '3000': None
    }
}
c.DockerSpawner.container_ip = '0.0.0.0'
c.DockerProcessSpawner.extra_create_kwargs = {
    'volume_driver': 'convoy',
    'command': '-directory /data/loopback -baseurl /{username}',
    'labels': {
       'interlock.hostname': 'local',
       'interlock.context_root': '/{username}'
   }
}
c.DockerProcessSpawner.volumes = {
   '{username}': '/data'
}
