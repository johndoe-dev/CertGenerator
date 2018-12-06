.. _pip: https://pip.pypa.io/en/stable/quickstart/


*************
CertGenerator
*************

Python module to generate key, certificate request and self signed
certificate

All generated certificate are located in certificate folder

Information
-----------

This can be used only with python(2.7)

Getting started
---------------

Install required modules, pip must be installed

**required** modules:
~~~~~~~~~~~~~~~~~~~~~

-  Click
-  pycparser
-  PyYAML

installing package using pip_


::

    $ pip install --editable .

or

::

   $ pip install -r requirements

Usage
-----

::

   Usage: cert [OPTIONS] COMMAND [ARGS]...

     A command line tool to create and read CSR and P12

   Options:
     -v, --verbose  Display only if necessary
     -d, --debug    Display all details
     --version      show version and exit
     -h, --help     Show this message and exit.

   Commands:
     config               Edit or read config ini
     create               Create a single CSR
     create-multiple      Create multiple certificate using csv file
     create-multiple-p12  Create multiple p12 using csv file
     create-p12           Create a simple p12 Need key file and pem file
     read                 Read csr or p12

On terminal you can use:

::

   python cert.py [ARGS]

or

::

   cert [ARGS]

Optional configurations file
----------------------------

**config.ini**
~~~~~~~~~~~~~~


2 sections in **config.ini**

- **default**
    - **log_file** is the log of file, where are referenced errors and warnings
- **config**
    -  **csvFile** is csv file to create several csr
    -  **yamlFile** is the yaml file to configure the datas of the csr

a third section **custom** can be added to change default app folder see config_.

In **config.ini**:

::

    [default]
    log_file = certgen.log

    [config]
    csvfile = serial.csv
    yamlfile = csr.yaml

.. _config:

======================================
Config add custom path to config ini
======================================

Read config ini

::

   $ cert config read

Change default path of app and default csv file path or csv name, it will add a custom section

::

   $ cert config edit [-cert [path/to/app folder]] [-csv [path/to/csv or csv file]]

Delete custom path of app or csv file, if no flag, it will delete the entire custom section

::

   $ cert config delete [[-cert] [-csv]]

**yaml**
~~~~~~~~

::

   CertGenerator
   |── csr.yaml

In **csr.yaml**:

::

   C: 'FR'
   O: 'FTW Enterprise'
   OU: 'IT'
   CN: 'Test'
   emailAddress: 'csr@test.com'

**csv**
~~~~~~~

::

   CertGenerator
   ├── csv
   │   └── serial.csv

-  You must add header column ‘serial’
-  you can create multiple csr using csv file in csv folder
-  The row from csv will be added in CN.

.. csv-table:: serial.csv
   :header: "serial"
   :widths: 10

   "SN123456"
   "SNjhgjkhkjh"
   "SDjhijoklklk"
   "SN654"

Create one certificate
~~~~~~~~~~~~~~~~~~~~~~

::

   $ cert create [FQDN]

using config.ini:

::

   $ cert create -c [FQDN]

Create multiple certificate
~~~~~~~~~~~~~~~~~~~~~~~~~~~

using csv file:

::

   $ cert create-multiple [-a] [--csv=[path/csv]]

‘-a’ is only if you use absolute path of –csv, if you don’t use absolute
path, it will search in csv folder

using config.ini:

::

   $ cert -c create-multiple [-a] [--csv=[path/csv]]

Please note, –csv override csv from config.ini

Read certificate
~~~~~~~~~~~~~~~~

::

   $ cert read [path/of/csr]