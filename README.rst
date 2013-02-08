FABRIC DEBIAN
=============

fabric-debian is a deployement tool for initialize, secure and deploy new debian server configured for website traficking. 
fabric-debian can deploy django-postgresql website in dedicated system user.
We have search and define **basic rules and best practice** used for **secure** and **configure** server, deploy and create web project.

Website development philosophy is to run in python virtualenv, with local virtual http server for serving web-pages from django. for that i use gunicorn and run it in virtualenv with linux user owner.

The physical server is free of all versions of python, django gunicorn etc... because we use confined virtual environnement.
Nginx is reverse-proxy for serve gunicorn request. 
On the same physical server we can serve more sites with differents version of django, gunicorn, python (case of django1.5)

Advertissement
--------------
Initialize server is ok. I've deactivate change owner of compilation tools, for immediately use this in production.
I want patch for professionnal use.
Deployement website is already at 80%, somes bug performs in like nginx virtualhost configuration deployement don't work perfectly

Exemples usage
--------------
*Deploy debian server after manual installation*

``fab -u root -p <password> -f server-initialize deploy_server``

*Deploy and serve a new django-postgresql website*

``fab -u root -p <password> -f server-initailize deploy_website``

VirtualBox testing
------------------
You can use this to test in virtualbox on debian server installation.
You must to configure private local network between virtualbox and host system, allocate IP 192.168.56.101 to the virtual server
and run it. Deployement is automaticaly configure to run on this address. to run in the real life, open the script and comment line with containe 192.168.56.101, and that's work

Choices
-------
- Python : Because is the most logical and effective programming high-level langage. I like the python philosophy, i think it's really good structured langage and logical
- Debian : Debian is very very stable linux distribute, he have large community, it's logical to use it on production server.
- Django : Django have a lot of re-usable packages, with large community. I win a lot of time to don't implements somes basicly components everytimes. I like the django-admin it's magical !!!

More
----
I've started fabric developpment evolution for can run this system on more linux / unix versions. For that i write some evolution to fabric package to can install with abstract handler of the host system package managers
