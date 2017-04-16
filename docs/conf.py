# Copyright (c) Moshe Zadka
# See LICENSE for details.
import os
import sys

up = os.path.dirname(os.path.dirname(__file__))
sys.path.append(up)

import caparg

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]
master_doc = 'index'
project = 'CapArg'
copyright = '2017, Moshe Zadka'
author = 'Moshe Zadka'
version = '17.4'
release = '17.4'
