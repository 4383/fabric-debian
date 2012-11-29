from fabric.api import *
import md5

env.hosts = ['192.168.56.101']

##########################################
# Create new server operation
##########################################
def initialize():
    """
    Full initialize of debia{
    """
    install_lib()

def install_lib():
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

##########################################
# Common operations
##########################################
def add_new_site():
    username = prompt('Username :')
    run('adduser {0}' . format(username))
    add_postgre_user(username)

def add_postgre_user(username):
    passphrase = prompt('Digest pass phrase :')
    password = md5.new()
    password.update(passphrase)

    run('su - postgres')
    run('''psql -c "CREATE USER {0} WITH PASSWORD '{1}';"''' . format(username, password.hexdigest()))
    run('''pqsl -c "CREATE DATABASE 'db'{0};"''' . format(username))
