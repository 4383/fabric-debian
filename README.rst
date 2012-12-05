FABRIC DEBIAN
=============

fabric-debian is a deployement tool for initialize, secure and deploy new debian server configured for website traficking. 
fabric-debian can deploy django-postgresql website in dedicated system user.
We have search and define **basic rules and best practice** used for **secure** and **configure** server, deploy and create web project.


Exemples usage
--------------
*Deploy debian server after manual installation*

``fab -u root -p <password> -f server-initialize initialize``

*Deploy and serve a new django-postgresql website*

``fab -u root -p <password> -f server-initailize add_new_website``
