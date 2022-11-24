import json
import os

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'package.json')) as package:
    package = json.load(package)
    __version__ = package['version']
if not __version__:
    __version__ = '0.0.0'
