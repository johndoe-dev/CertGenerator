.. _pip: https://pip.pypa.io/en/stable/quickstart/


*************
CertGenerator
*************

Python module to generate key, certificate request, self signed
certificate and p12 certificate

Information
-----------

This can be used only with python2.7

Getting started
---------------

**required** modules:
~~~~~~~~~~~~~~~~~~~~~

-  Click
-  pycparser
-  PyYAML

Installing package using pip_

::

    $ pip install CertGenerator

Usage
-----

::

    Usage: cli.py [OPTIONS] COMMAND [ARGS]...

      A command line tool to create and read CSR and P12

    Options:
      -v, --verbose  Display only if necessary
      -d, --debug    Display all details
      -V, --version  show version and exit
      -h, --help     Show this message and exit.

    Commands:
      config               Edit or read config ini
      create               Create a single CSR
      create-multiple      Create multiple certificate using csv file
      create-multiple-p12  Create multiple p12 using csv file
      create-p12           Create a simple p12 Need key file and pem file
      init                 Create or edit certificate folder and csv file Add...
      read                 Read csr or p12


PRE-CONFIGURATION
-----------------
Configuration files
~~~~~~~~~~~~~~~~~~~
**serial.csv**

.. csv-table:: serial.csv
   :header: "serial"
   :widths: 50

   "test1"
   "test2"
   "test3"

**config.ini**


Create default folder
    * Default folder => **$HOME/Documents/CertGenerator/**
    * copy default csv file to **$HOME/Documents/CertGenerator/csv/serial.csv**
    * copy yaml file to **$HOME/Documents/CertGenerator/csr.yaml**

::

    $ cert init

To change default folder or default csv:

::

    $ cert init -cert [path/of/folder] -csv [path/of/csv/file]

or

::

    $ cert config edit -cert [path/of/folder] -csv [path/of/csv/file]

To edit yaml file:
    * Enter the desired subject
    * Enter "-" to keep empty
    * If you want to create multiple csr using serial.csv, don't use Commmon Name => just enter "-" to keep empty
    * **Note**: You always have old csr.yaml in folder under format csr.yam_[date od modification]

::

    $ cert config edit-yaml



CONFIGURATION
-------------

Create csr
----------

Create one csr
~~~~~~~~~~~~~~

* Use -c if you want to use csr.yaml to create csr
* The key and csr files will be created in {folder}/certificate/csr/
* Example: With the command below it will create
    * {folder}/certificate/csr/test/test.csr
    * {folder}/certificate/csr/test/test.key

::

    $ cert create test -c

Create multiple csr
~~~~~~~~~~~~~~~~~~~

* Use -c if you want to use csv file and csr.yaml

::

    * cert create-multiple -c


Create p12
----------

Create one p12
~~~~~~~~~~~~~~

* You need pem file  and key file:

::

    $ cert create-p12 test.p12 --pem [path/of/pem file] --key [path/of/key file] -pass [password(default:3z6F2Xfc)]

Create multiple p12
~~~~~~~~~~~~~~~~~~~

* for creating multiple p12: pem file, key file and p12 must have the same name
* Example if you create test1.p12 test2.P12 ...:
    * In the csv file, you must have test1 test2 ...
    * The pem files must be test1.pem test2.pem ...
    * The key files must be test1.key test2.key ...
    * It will search key files in folder/certificate/csr/

::

    $ cert create-multiple-p12 -c --pem-folder [path/of/pem folder]

If you want to use an other folder to search key files, add --key-folder:

::

    $ cert create-multiple-p12 -c --pem-folder [path/of/pem folder] --key-folder [path/of/key folder]

.. include:: CHANGES.txt

Links
-----

-  Releases: https://pypi.org/project/CertGenerator/
-  Code: https://github.com/johndoe-dev/CertGenerator.git

