FABRIC DEBIAN
=============

fabric-debian is a deployement tool for initialize, secure and deploy new debian server configured for website traficking. 
fabric-debian can deploy django-postgresql website in dedicated system user.
We have search and define **basic rules and best practice** used for **secure** and **configure** server, deploy and create web project.

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
