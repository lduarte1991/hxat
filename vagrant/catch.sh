#!/bin/bash
# Installs catch database system-wide after the base system has been provisioned.
#
# URLS: 
# - https://github.com/annotationsatharvard/catcha
# - http://catcha.readthedocs.io/en/latest/admin-guide/installation/ 

MYSQL_ROOT_PASSWORD=devrootpass
CATCH_RELEASE_URL=https://github.com/annotationsatharvard/catcha/releases/download/v0.5.12/catch.war

# Install system packages
sudo debconf-set-selections <<< "mysql-server mysql-server/root_password password $MYSQL_ROOT_PASSWORD"
sudo debconf-set-selections <<< "mysql-server mysql-server/root_password_again password $MYSQL_ROOT_PASSWORD"
sudo apt-get -y install openjdk-7-jre tomcat7 tomcat7-admin mysql-server

# Setup database 
mysql -uroot -p$MYSQL_ROOT_PASSWORD -e 'CREATE DATABASE catch DEFAULT CHARSET UTF8;'
mysql -uroot -p$MYSQL_ROOT_PASSWORD -e 'GRANT ALL ON catch.* to 'catch'@'localhost' IDENTIFIED BY "catch";'

# Setup Catch config
sudo service tomcat7 stop
if [ ! -e /usr/share/tomcat7/.grails ]; then
	sudo mkdir -v /usr/share/tomcat7/.grails
fi

sudo echo <<__END > /usr/share/tomcat7/.grails/catch-config.properties
# Database Configuration
dataSource.url=jdbc:postgresql://localhost:5432/catch?useUnicode=yes&characterEncoding=UTF-8&autoReconnect=true
dataSource.username=catch
dataSource.password=catch

# CATCH Configuration
af.shared.name=CATCH-A
af.shared.title=CATCH-A, Annotations at Harvard
af.shared.logo.title=CATCH
af.shared.logo.subtitle=Annotation Hub
af.shared.copyright.label=Annotations @ Harvard 
af.shared.copyright.link=http://www.annotations.harvard.edu/
af.security.initialize.user=true
af.security.moderation.user.request=true
af.node.organization=Massachusetts General Hospital
af.node.administrator.name=Dr. Paolo Ciccarese
af.node.administrator.email.to=paolo.ciccarese@gmail.com
af.node.administrator.email.display=paolo dot ciccarese at gmail.com
af.node.base.url=http://localhost:8080/catch/
__END

sudo echo 'export CATALINA_OPTS="-Xms512m -Xmx512m -XX:MaxPermSize=256m"' > /usr/share/tomcat7/bin/setenv.sh
sudo chown -R tomcat7 /usr/share/tomcat7/
sudo chmod +x /usr/share/tomcat7/bin/setenv.sh
sudo wget -q -O /var/lib/tomcat7/webapps/catch.war $CATCH_RELEASE_URL
sudo service tomcat7 start # tail /var/log/tomcat7/catalina.out
