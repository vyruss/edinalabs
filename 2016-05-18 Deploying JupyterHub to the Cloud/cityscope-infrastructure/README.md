Cityscope project infrastructure
================================

## Requirements
- Ansible
- aws command line utility and ~/.aws/credentials
- Boto
- encfs
- the cityscope-jupyterhub repository as sibling repository (under the same path)
```
├── cityscope-infrastructure
└── cityscope-jupyterhub
```

# Before running any task

#### Inventory
If you have a ```production``` file copy it to ```inventory/production``` otherwise copy ```inventory/production.sample``` to ```inventory/production``` it will be updated with the hosts after doing the provisioning.

#### Keys vault
All the sensitive information is encrypted using encfs, in order to decrypt you need the vault password and to run:

```
./mount_vault.sh
```

## Tasks

### Provisioning the docker swarm
```
  ansible-playbook provision-swarm-ec2.yml
```

### Configuring the docker swarm
```
  ansible-playbook config-swarm.yml
```

### Provisioning jupyterhub
```
  ansible-playbook provision-jupyterhub-ec2.yml
```

### Configuring jupyterhub
```
  ansible-playbook config-jupyterhub.yml
```
