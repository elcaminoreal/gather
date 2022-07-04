import os
import sys

up = os.path.dirname(os.path.dirname(__file__))
sys.path.append(up)

import gather

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

root_doc = 'index'
project = 'Gather'
copyright = 'Copyright (c) Moshe Zadka'
author = 'Moshe Zadka'
version = ''

exclude_patterns = ['.ipynb_checkpoints/**']
