from distutils.core import setup
import py2exe
import os
import sys
import pygtk
import matplotlib.backends.backend_gtkagg
import matplotlib
import glib
import gobject
import warnings
from email.header import Header
import email
import email.message
import scipy
import numpy
import glib

__import__('gtk')
m = sys.modules['gtk']
gtk_base_path = m.__path__[0]
includes=[]
mydata=[]
for value in matplotlib.get_py2exe_datafiles():
    mydata.append(value)
otherdata=['tesidog.glade']
for value in otherdata:
    mydata.append(value)

setup(
    name = 'Tesi Dog App',
    description = 'Dog viewer',
    version = '1.0',

    windows = [
                  {
                      'script': 'tesiapp.py',
                  }
              ],

    options = {
                  'py2exe': {
                      'compressed':1,
                      'optimize':2,
                      'ascii':True,
                      'packages':'encodings',
                      'includes': includes +["numpy", "numpy.core", "glib","matplotlib.backends.backend_tkagg", "matplotlib.backends.backend_gtkagg","matplotlib.backends.backend_gtk", 'email', 'email.header', 'email.message', 'cairo', 'pango', 'pangocairo', 'atk', 'gobject', 'gio', 'glib', 'gtk.keysyms', 'email.mime.*'],
                      'excludes': [],
                      'bundle_files':3
                  }
              },

    data_files=mydata,
    zipfile=None
)
