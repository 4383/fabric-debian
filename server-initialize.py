# Author Herve BERAUD
from fabric.api import *
import md5
import os
import io

# VirtualBox local bridge between host and guest
# Replace by your IP
env.hosts = ['192.168.56.102']
CONFIG_PATH = '{0}{1}config{1}' . format(os.getcwd(), os.sep)
TMP_PATH = '{0}{1}tmp{1}' . format(os.getcwd(), os.sep)

##########################################
# Create new server operation
##########################################
def initialize():
    """
    Full initialize of debian server deployement
    Only make basic action of the root user for make
    functional server
    """
    install_app()
    setup_ssh()
    user_admin()
    setup_firewall()

def install_app():
    """
    Install all apps to have functional server, that
    works for python-django website with postgresql databse
    """
    apps = [
        'vim-nox',
        'python-pip',
        'python-virtualenv',
        'python-setuptools',
        'python-psycopg2',
        'postgresql-8.4',
        'apache2',
        'libapache2-mod-wsgi'
        'makejail',
    ]

    apt = ''
    for app in apps:
        apt = '{0} {1}' . format(apt, app)
    run('aptitude update')
    run('aptitude upgrade')
    run('aptitude install {0}' . format(apt))

def user_admin():
    """
    Create administrator other than root
    """
    username = prompt('Username for admin : ')
    add_new_user(username)
    run('echo AllowUsers {0} >> /etc/ssh/sshd_config' . format(username))
    run('/etc/init.d/ssh restart')

def setup_firewall():
    """
    Initialize and configure iptable firewall.
    """
    path = '{0}firewall.sh' . format(CONFIG_PATH)
    put(path, '~', mode=0700)
    run('echo "/root/firewall.sh" >> /etc/rc.local')
    run('sh ~/firewall.sh')

def setup_ssh():
    """
    Initialize and configure SSH.
    root login is deactivated
    restart after create new user account admin
    """
    path = '{0}sshd_config' . format(CONFIG_PATH)
    put(path, '/etc/ssh')

def jail_apache():
    """
    Secure apache by chroot
    http://www.debian.org/doc/manuals/securing-debian-howto/ap-chroot-apache-env.fr.html

    /!\ Not implemented for moment
    """
    pass

##########################################
# Common operations
##########################################
def add_new_site():
    """
    Add a new website on the specified server.
    The website live on new account user on this server.
    The path to source is : /home/<username>/source
    Create a new postgre user in relation with debian user.
    """
    username = prompt('Username :')
    add_new_user(username)
    add_postgre_user(username)
    add_httpd_vhost(username)

def add_new_user(username=None):
    """
    """
    if not username:
        username = prompt('Username :')
    run('adduser {0}' . format(username))

def add_postgre_user(username):
    """
    Add new postgre user <username>
    The password is a digest md5 of user passphrase
    """
    passphrase = prompt('Digest pass phrase :')
    password = md5.new()
    password.update(passphrase)

    actions = [
        '''psql -c "CREATE USER {0} WITH PASSWORD '{1}';"''' . format(username, password.hexdigest()),
        '''psql -c "CREATE DATABASE db{0};"''' . format(username),
        '''psql -c "GRANT ALL PRIVILEGES ON DATABASE db{0} to {0};"''' . format(username)
    ]

    for command in actions:
        sudo(command, user='postgres')

def add_httpd_vhost(username='vrp-online'):
    """
    Add a new virtualhost to httpd with using template apache
    """
    # Create the new config file for writing
    config = io.open('{0}{1}.conf' . format(TMP_PATH, username), 'w')

    # Read the lines from the template, substitute the values, and write to the new config file
    for line in io.open('{0}apache' . format(CONFIG_PATH), 'r'):
        line = line.replace('$path_site', '/home/{0}/www/' . format(username))
        line = line.replace('$site_domain', '{0}.com' . format(username))
        config.write(line)

    # Close the files
    config.close()
