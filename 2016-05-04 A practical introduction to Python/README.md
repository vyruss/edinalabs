## 2016-05-04 A practical introduction to Python

* The example code shown in the workshop is in `doit-with-copy.py`
* The sample data is in the xzipped xml file `sample.xml.xz`

### Preparation
1. Install Virtualenv for Python
  * For Ubuntu/Debian:
    ```
    sudo apt-get install python-virtualenv
    ```
    
  * For CentOS/RHEL:
    ```
    sudo rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
    sudo yum -y install python-virtualenv
    ```

2. Create a Python virtual environment and enter it
  ```
  virtualenv ve
  . ve/bin/activate
  ```
  
3. Update `pip` and install dependencies
  ```
  pip install --upgrade pip
  pip install xmltodict
  ```
  
4. Install PostgreSQL and Psycopg2 dependency
  * For Ubuntu/Debian:
    ```
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    sudo apt-get install wget ca-certificates
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get install postgresql-9.5 python-psycopg2
    ```
    
  * For CentOS/RHEL:
    ```
    sudo rpm -Uvh https://download.postgresql.org/pub/repos/yum/9.5/redhat/rhel-7-x86_64/pgdg-centos95-9.5-2.noarch.rpm
    sudo yum -y install postgresql95 postgresql95-server python-psycopg2
    ```
    
5. Create a Postgres DB called `marc` owned by user `marc`
  * For Ubuntu/Debian:
    * Edit your `/etc/postgresql/9.5/main/pg_hba.conf`

      ```
      local   all             postgres                                trust
      local   all             all                                     trust
      ```
    * Create DB and user
      ```
      sudo -u postgres "createuser marc"
      sudo -u postgres "createdb marc -O marc"
      ```
    
  * For CentOS/RHEL:
    * Edit your `/var/lib/pgsql/9.5/data/pg_hba.conf`

      ```
      local   all             postgres                                trust
      local   all             all                                     trust
      ```
    * Create DB and user

      ```
      sudo -u postgres "createuser marc"
      sudo -u postgres "createdb marc -O marc"
      ```
    
6. Decompress sample data
  ```
  xz -d sample.xml.xz
  ```
