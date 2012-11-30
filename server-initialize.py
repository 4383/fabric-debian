from fabric.api import *
import md5

env.hosts = ['192.168.56.101']

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

def install_app():
    """
    Install all apps to have functional server, that
    works for python-django website with postgresql databse
    """
    apps = [
        'python-pip',
        'python-virtualenv',
        'postgresql-8.4',
        'apache2',
    ]

    apt = ''
    for app in apps:
        apt = '{0} {1}' . format(apt, app)
    run('aptitude update')
    run('aptitude upgrade')
    run('aptitude install {0}' . format(apt))

def set_firewall():
    """
    Initialize and configure iptable firewall.
    """

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
    run('adduser {0}' . format(username))
    add_postgre_user(username)
    add_httpd_vhost(username)

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

def add_httpd_vhost(username):
    """
    Add a new virtualhost to httpd
    """
