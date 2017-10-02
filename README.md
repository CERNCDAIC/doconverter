# CERN document conversion service

The conversion service intends to automatically convert a number of application formats, input ones,
to a different format, output ones, usually PDF or PDF/A though evolution of the service is always possible
and more variety on terms of input and output file format could be possible. It's thought to do so asynchronously using
a REST API.

## Architecture

The two main components of the framework are a web fronted and worker nodes. Worker nodes are running on Windows as
most of the functionality of the document conversion service deals with office applications. Web server and worker nodes
don't run in the same server and communication about conversion jobs is done using a common file system.
[EOS](http://eos.web.cern.ch/) is a CERN developed file system that can be accessed from Linux like and Windows
operating systems.

Both components have been developed using Python3.
A PostgreSQL database is used to keep accounting of jobs requested and results.

## Setup

The application expects this structure on a windows server:
```
c:\doconverter
              \logs
              \config\
                      doconverter.ini
                      logging.conf
              \files
              \cert
              \doconverter
```

A sample of doconverter.ini and logging.conf can be found in the project.

Possible setup on a Windows machine
```
# Activate appropiate environment
workon doconverter
cd c:\doconverter
git clone https://github.com/CERNCDAIC/doconverter.git
cd doconverter
pip install -r requirement.txt
# This is required to run COM. Cant be added as it will fail image build on Openshift (Linux)
pip install pypiwin32

# Database setup, PostgreSQL user and schema should be available
python
from doconverter.models.extensions import db
from doconverter.models.Taskdb import Taskdb
from doconverter.models.Result_Conversion import Result_Conversion
db.drop_all()
db.create_all()

# Run converter
python .\engines\converter_daemon.py --n 2
#
```

## Software

The project relies in several packages for conversion:
  - [Neevia DocPro converter](https://neevia.com/) a license is required, though a test software is available. Most
  office like conversions are done using this software. It requires also that those applications be installed on the
  server e.g. Microsoft Office, Open Office, Autocad, etc..
  - [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) it converts image files to a searchable PDF.
  - [SharepointDesigner 2007](https://www.microsoft.com/en-us/download/details.aspx?displaylang=en&id=21581) it converts
   images and PDF files to a searchable PDF. It uses Neevia COM.
  - [HPGL-Viewer](http://service-hpglview.web.cern.ch/service-hpglview/) it converts PLT files to PDF.

