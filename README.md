Learning Registry Installation and Configuration
================================================

License & Copyright
===================
Copyright 2011 SRI International

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Installation on Turnkey Core (Ubuntu 10.04 LTS)
===============================================

## Configure apt sources ##

* Edit the sources list       

>       sudo vim /etc/apt/source.list.d/sources.list
    
* Add deb restrticted and multiverse, plus add deb-src for all:

>       deb http://us.archive.ubuntu.com/ubuntu lucid main universe restricted multiverse
>       deb http://us.archive.ubuntu.com/ubuntu lucid-updates main universe restricted multiverse
>       deb-src http://us.archive.ubuntu.com/ubuntu lucid main universe restricted multiverse
>       deb-src http://us.archive.ubuntu.com/ubuntu lucid-updates main universe restricted multiverse

* Update apt sources

>       sudo apt-get update
    
    
## Install curl ##

* Use apt-get to install curl

>       sudo apt-get install libcurl3 curl
    
    
## Install Python setup tools ##

* Install Python easy_setup

>       sudo apt-get python-pkg-resources python-setuptools
    
    
## Install CouchDB ##

* Build CouchDB dependencies

>       sudo apt-get build-dep couchdb

* Install other dependencies

>       sudo apt-get install xulrunner-dev libicu-dev libcurl4-gnutls-dev libtool

* Then create /etc/ld.so.conf.d/xulrunner.conf. 

>   a. To check what XULRunner version you have installed:

>       xulrunner -v

>   b. Configure xulrunner

>   >   i. Edit the xulrunner.conf

>   >       sudo vi /etc/ld.so.conf.d/xulrunner.conf
          
>   >   ii. Add the following edits, replacing the x.x.x.x with your version number.
    
>   >       /usr/lib/xulrunner-x.x.x.x
>   >       /usr/lib/xulrunner-devel-x.x.x.x

>   c. Update ldconfig

>       sudo /sbin/ldconfig

* Download CouchDB from http://couchdb.apache.org/downloads.html.

* Untar (decompress) the source file:
 
>       tar -zxvf apache-couchdb-x.x.x.tar.gz

* Change into the expanded directory: 

>       cd apache-couchdb-x.x.x

* Install SpiderMonkey (see below)

* Configure the build:  
   
>       LDFLAGS="$(pkg-config mozilla-js --libs-only-L)" CFLAGS="$(pkg-config mozilla-js --cflags)" ./configure
    
* Build CouchDB:

>       make

* Fix any errors

* Install CouchDB to default location:

>       sudo make install

* Add couchdb user account

* change file ownership from root to couchdb user and adjust permissions

>       chown -R couchdb: /usr/local/var/{lib,log,run}/couchdb /usr/local/etc/couchdb
>       chmod 0770 /usr/local/var/{lib,log,run}/couchdb/
>       chmod 664 /usr/local/etc/couchdb/*.ini
>       chmod 775 /usr/local/etc/couchdb/*.d
    
* install init script and start couchdb

>       cd /etc/init.d
>       ln -s /usr/local/etc/init.d/couchdb couchdb
>       /etc/init.d/couchdb start
        
* configure couchdb to start on system start

>       update-rc.d couchdb defaults

* Verify couchdb is running       

>       curl http://127.0.0.1:5984/

* To accesses futon remotely and run tests, update the bind address in local.ini:    

>       sudo vim /usr/local/etc/couchdb/local.ini
>            [httpd]
>            ; Bind to all addresses
>            bind_address = 0.0.0.0

* Restart couchdb

>       sudo service couchdb restart
    
    
## Install SpiderMonkey ##

* Get one of the source tarballs from http://ftp.mozilla.org/pub/mozilla.org/js/ (1.7.0 or 1.8.0-rc1 will do).

* Unpack the tarball. Note that once extracted the source are in the directory "js", without the expected version suffix.

* Go to the js/src directory.

>       cd js/src

* Build SpiderMonkey. There is no default Makefile, use Makefile.ref. The default build is debug, use BUILD_OPT=1 for an optimized build.

>       make BUILD_OPT=1 -f Makefile.ref

* Install SpiderMonkey. Instead of "install" the target to use is "export". Instead of PREFIX the target directory is specified with JS_DIST.

>       sudo make BUILD_OPT=1 JS_DIST=/usr/local -f Makefile.ref export


## Install Python virtualenv and Pylons ##

* Install virtualenv

>       sudo easy_install virtualenv

* Create a user for learningregistry and su to user

>       su learningregistry

* Create a directory for the virtualenv

>       mkdir virtualenv
>       cd virtualenv

* Create virtualenv for LR

>       virtualenv --distribute lr
>       cd lr/bin/

* Install LR Python deps

>       ./pip install pylons
>       ./pip install flup
>       ./pip install pyparsing
>       ./pip install --upgrade couchdb

  
## Configure Nginx - Should be preinstalled on Ubuntu ##

* Backup your original nginx.conf file

>       sudo cp /etc/nginx/nginx.conf /etc/nginx.conf.bak

* Copy the ngnix.conf file from repository

>       sudo cp nginx.conf /etc/nginx/nginx.conf

## Start LR code ##

* From your virtualenv directory start paster where */home/learningregistry/virtualenv/lr* is my path to virtualenv.

>       /home/learningregistry/virtualenv/lr/bin/paster serve --reload development.ini &



            