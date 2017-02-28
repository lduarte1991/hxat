#!/bin/bash
PROJECT=annotationsx
USER=vagrant
HOME=/home/vagrant

# Update packages
sudo apt-get update
sudo apt-get -y autoremove

# Install system packages
sudo apt-get -y install build-essential libffi-dev
sudo apt-get -y install libxslt1-dev libxml2 libxml2-dev
sudo apt-get -y install openssl libcurl4-openssl-dev
sudo apt-get -y install git curl wget unzip
sudo apt-get -y install python-dev python-pip python-setuptools redis-server
sudo apt-get -y install postgresql postgresql-contrib libpq-dev

# Install system python dependencies (project-specific will be installed in a virtualenv)
sudo pip install virtualenv
sudo pip install urllib3[secure]

# Setup database 
sudo -u postgres -i psql -d postgres -c "DROP DATABASE IF EXISTS $PROJECT"
sudo -u postgres -i psql -d postgres -c "DROP USER IF EXISTS $PROJECT"
sudo -u postgres -i psql -d postgres -c "CREATE USER $PROJECT WITH PASSWORD '$PROJECT'"
sudo -u postgres -i psql -d postgres -c "CREATE DATABASE $PROJECT WITH OWNER $PROJECT"

sudo -u $USER -s bash

# Ensure github.com ssh public key is in $HOME/.ssh/known_hosts file
chmod 700 $HOME/.ssh
if ! grep -sq github.com $HOME/.ssh/known_hosts; then
	ssh-keyscan github.com >> $HOME/.ssh/known_hosts
fi
chmod 744 $HOME/.ssh/known_hosts

# Create symlink from home dir to /vagrant as a convenience 
if [ ! -h $HOME/$PROJECT ]; then
	ln -sv /vagrant $HOME/$PROJECT
fi

# Create virtualenv
mkdir -pv $HOME/python_environments
virtualenv $HOME/python_environments/$PROJECT
. $HOME/python_environments/$PROJECT/bin/activate
pip install -r $HOME/$PROJECT/requirements.txt 

# Setup $HOME/.bash_profile to automatically source the environment settings 
echo "export DJANGO_SETTINGS_MODULE=$PROJECT.settings.aws" > $HOME/.env
echo ". $HOME/python_environments/$PROJECT/bin/activate" >> $HOME/.env
if ! grep -sq ". $HOME/.env" $HOME/.bash_profile; then
	echo ". $HOME/.env" >> $HOME/.bash_profile
fi
