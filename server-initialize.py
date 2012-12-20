# -*- coding: utf-8 -*-
"""
author : Hervé BERAUD
file : server-initialize.py
"""
from fabric.api import *
import md5
import os
import io
import sys
import re

# VirtualBox local bridge between host and guest only for testing
# Replace by your server IP
#env.hosts = ['192.168.56.101']
CONFIG_PATH = '{0}{1}config{1}' . format(os.getcwd(), os.sep)
TMP_PATH = '{0}{1}tmp{1}' . format(os.getcwd(), os.sep)

##########################################
# Utils
##########################################
def email_is_requiered(func):
    """
    Set email if not defined
    """
    def wrapper(**kwargs):
        """
        Handle args of decorated function
        """
        email = kwargs.get('email', None)
        while email :
            if not email:
                email = prompt('Give an valide email')
        return func(email)
    return wrapper

def root_is_required(func):
    """
    Required user root for launching function
    """
    if env.user != 'root':
        print('Function require root user !')
        sys.exit(1)
    return func
##########################################
# Create new server operation
##########################################
@root_is_required
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
    setup_fail2ban(email='test')
    setup_rootkit_secure(None)
    secure_tools()
    remove_bad_services()
    run('echo "exit 0" >> /etc/rc.local')
    run('reboot')

@root_is_required
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

@root_is_required
def install_app():
    """
    Install all apps to have functional server, that
    works for python-django website with postgresql databse
    """
    apps = [
        # Security
        'rkhunter',
        'fail2ban',
        'makejail',
        'knockd',
        # Python
        'python-pip',
        'python-virtualenv',
        'python-setuptools',
        'python-psycopg2',
        'python-imaging',
        # Server
        'postgresql-8.4',
        'apache2',
        'libapache2-mod-wsgi',
        'git-core',
        # Mailing
        'postfix',
        'sendmail',
        # Common
        'sed',
        'vim-nox', # Vim with python supports
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
@root_is_required
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
    os.remove(config_file)

##########################################
# Common operations for secure
##########################################
@root_is_required
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
    os.remove(config_file)

@root_is_required
def setup_firewall():
    """
    Initialize and configure iptable firewall.
    """
    path = '{0}firewall.sh' . format(CONFIG_PATH)
    put(path, '/etc/init.d/')
    #run('echo "/root/firewall.sh" >> /etc/rc.local')
    run('update-rc.d firewall.sh defaults')

@root_is_required
def setup_ssh():
    """
    Initialize and configure SSH that's listen on port 6060.
    """
    path = '{0}sshd_config' . format(CONFIG_PATH)
    put(path, '/etc/ssh')

@root_is_required
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

@root_is_required
@email_is_requiered
def setup_rootkit_secure():
    """
    Initialize, configure rootkit hunting with chkrootkit and rootkithunter
    """
    config_file = '/etc/default/rkhunter'
    run('cp {0} {0}.old' . format(config_file))
    run('sed s/root/{1}/ {0}.old > {0}' . format(config_file, email))
    run('rm -rf {0}.old' . format(config_file))

@root_is_required
def secure_tools():
    """
    Secure and change access rule for compilating tools and
    dangerous system tools.
    Only root can use this.
    """
    run('chmod o-x /usr/bin/gcc*')
    run('chmod o-x /usr/bin/make')
    run('chmod o-x /usr/bin/dpkg*')
    run('chmod o-x /usr/bin/apt-get')

@root_is_required
def remove_bad_services():
    """
    Remove dangerous service not used
    """
    run('/etc/init.d/portmap stop')
    run('/etc/init.d/nfs-common stop')
    run('update-rc.d -f portmap remove')
    run('update-rc.d -f nfs-common remove')
    run('update-rc.d -f inetd remove')
    run('aptitude remove portmap')
    run('aptitude remove ppp')

def test():
    setup_fail2ban()

@root_is_required
@email_is_requiered
def setup_fail2ban(email):
    """
    Initialize, configure fail2ban
    """
    config_file = '/etc/fail2ban/jail.local'
    run('sed /destemail/d /etc/fail2ban/jail.conf > {0}' . format(config_file))
    rules = [
        "destemail = {0}" . format(email),
        "[ssh_perso]",
        "enabled = true",
        "port = 6060",
        "filter = sshd",
        "logpath = /var/log/auth.log",
        "maxretry = 6",
    ]
    for rule in rules:
        run('echo {0} >> {1}' . format(rule, config_file))
