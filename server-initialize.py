# -*- coding: utf-8 -*-
"""
author : Hervé BERAUD
"""
from fabric.api import *
import md5
import os
import io

# VirtualBox local bridge between host and guest only for testing
# Replace by your server IP
env.hosts = ['192.168.56.101']
CONFIG_PATH = '{0}{1}config{1}' . format(os.getcwd(), os.sep)
TMP_PATH = '{0}{1}tmp{1}' . format(os.getcwd(), os.sep)
ENV = 'DEV'

##########################################
# Create new server operation
##########################################
def deploy_server():
    """
    Full initialize of debian server deployement
    Only make basic action of the root user for make
    functional server
    """
    install_app()
    run('sed /exit/d /etc/rc.local > /etc/rc.local')
    setup_ssh()
    setup_port_knocking()
    setup_firewall()
    setup_postfix()
    run('echo "exit 0" >> /etc/rc.local')
    run('reboot')

def deploy_website():
    """
    Add a new website on the specified server.
    The website live on new account user on this server.
    The path to source is : /home/<username>/source
    Create a new postgre user in relation with debian user.
    """
    username = prompt('Username :')
    add_new_user(username)
    init_git(username)
    add_postgre_user(username)
    add_httpd_vhost(username)

def install_app():
    """
    Install all apps to have functional server, that
    works for python-django website with postgresql databse
    """
    apps = [
        'rkhunter',
        'fail2ban',
        'vim-nox',
        'python-pip',
        'python-virtualenv',
        'python-setuptools',
        'python-psycopg2',
        'python-imaging',
        'postgresql-8.4',
        'apache2',
        'libapache2-mod-wsgi',
        'git-core',
        'makejail',
        'knockd',
        'sed',
        'postfix',
        'sendmail',
    ]

    apt = ''
    for app in apps:
        apt = '{0} {1}' . format(apt, app)
    run('aptitude update')
    run('aptitude upgrade')
    run('aptitude install {0}' . format(apt))

##########################################
# Common operations for website
##########################################

def add_new_user(username=None):
    """
    Add new system user account
    """
    if not username:
        username = prompt('Username :')
    run('adduser {0}' . format(username))
    ssh_rsa_authentification_for_user(username)

def ssh_rsa_authentification_for_user(username):
    """
    Configure ssh rsa authentification
    """
    if not os.path.isfile('~/.ssh/id_rsa.pub'):
        local('ssh-keygen -t rsa')
    sudo('mkdir ~/.ssh', user=username)
    put('~/.ssh/id_rsa.pub', '/home/{0}/.ssh' . format(username))
    run('chown -R {0}:{0} /home/{0}/.ssh' . format(username))
    sudo(
        'cat /home/{0}/.ssh/id_rsa.pub >> /home/{0}/.ssh/authorized_keys' . format(username),
        user=username
    )

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

def init_git(username):
    """
    Add a new git repository for current web site source code.
    Upload archive format at tar.gz to server
    Create and initialize git repository, add source file to this
    """
    path_source = prompt('Local path to your source folder : ')

    home = '/home/{0}' . format(username)
    # Create and init repository
    with cd(home):
        with settings(sudo_user=username):
            sudo('mkdir -p git')
            with cd('{0}/git' . format(home)):
                sudo('git --bare init')
                run('chown -R {0}:{0} .' . format(username))
                sudo('chmod o-w git')
    local('git remote rm server_prod {0}' . format(path_source))
    local('git remote add server_prod {0}@{1}:6060/git {2}' . format(username, env.hosts[0], path_source))
    local('git push server_prod master {0}' . format(path_source))

def add_httpd_vhost(username):
    """
    Add a new virtualhost to httpd with using template apache
    """
    # Create the new config file for writing
    config_file = '{0}{1}' . format(TMP_PATH, username)
    config = io.open(config_file, 'w')
    if not config:
        print('Configuration is broken. Config fill not found')

    # Read the lines from the template, substitute the values, and write to the new config file
    for line in io.open('{0}apache.conf' . format(CONFIG_PATH), 'r'):
        line = line.replace('$path_site', '/home/{0}/www' . format(username))
        line = line.replace('$site_domain', '{0}.com' . format(username))
        config.write(line)

    # Close the files
    config.close()
    put(config_file, '/etc/apache2/site-available')

    run('a2ensite {0}' . format(username))
    run('service apache2 restart')
    if 'DEV' ==  ENV:
        os.remove(config_file)

##########################################
# Common operations for secure
##########################################
def setup_port_knocking():
    """
    Initialize and configure port knocking service
    """
    open_code_sequence = prompt('Port Knocking open code sequence (example : 111,222,333) : ')
    close_code_sequence = prompt('Port Knocking close code sequence (example : 333,222,111) : ')
    config_file = '{0}knockd.conf' . format(TMP_PATH)
    config = io.open(config_file, 'w')
    if not config:
        print('Configuration is broken. Config fill not found')

    # Read the lines from the template, substitute the values, and write to the new config file
    for line in io.open('{0}knockd.conf' . format(CONFIG_PATH), 'r'):
        line = line.replace('$open_code_sequence', open_code_sequence)
        line = line.replace('$close_code_sequence', close_code_sequence)
        config.write(line)

    # Close the files
    config.close()
    put(config_file, '/etc')
    run('mv /etc/default/knockd /etc/default/knockd.save')
    put('{0}knockd' . format(CONFIG_PATH), '/etc/default')
    run('echo "service knockd restart" >> /etc/rc.local')
    run('service knockd restart')

    if 'DEV' ==  ENV:
        os.remove(config_file)

def setup_firewall():
    """
    Initialize and configure iptable firewall.
    """
    path = '{0}firewall.sh' . format(CONFIG_PATH)
    put(path, '/etc/init.d/')
    #run('echo "/root/firewall.sh" >> /etc/rc.local')
    run('update-rc.d firewall.sh defaults')

def setup_ssh():
    """
    Initialize and configure SSH that's listen on port 6060.
    """
    path = '{0}sshd_config' . format(CONFIG_PATH)
    put(path, '/etc/ssh')

def setup_postfix():
    """
    Initialize configure and secure postfix
    Server domain is required because we configure
    server for hosting multiple website. So you must
    set domain for routing mail from system and not from specific website
    """
    domain = prompt('Your server domain : ')
    run('postconf -e "myorigin = {0}"' . format(domain))
    run('postconf -e "myhostname = {0}.{1}"' . format(env.host_string, domain))
    run('postfix reload')
    for line in io.open('{0}smtp_secure.conf' . format(CONFIG_PATH), 'r'):
        run('echo "{0}" >> /etc/postfix/main.cf' . format(line))

def setup_rootkit_secure():
    """
    Initialize, configure rootkit hunting with chkrootkit and rootkithunter
    """

