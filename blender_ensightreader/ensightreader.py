"""
Placeholder for the real `ensightreader` module, which is located
in git submodule pointing to the `ensightreader` repository.

At build time, content of this file is replaced with "ensight-reader/ensighreader.py".

For development, we just re-export the real `ensightreader` module here.

"""

import sys, os.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../ensight-reader"))
from ensightreader import *
