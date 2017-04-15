"""
Example wsgi python file for pythonAnywhere hosting.

# This file contains the WSGI configuration required to serve up your
# web application at http://YourSubdomain.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.

# +++++++++++ GENERAL DEBUGGING TIPS +++++++++++
# getting imports and sys.path right can be fiddly!
# We've tried to collect some general tips here:
# https://www.pythonanywhere.com/wiki/DebuggingImportError

# +++++++++++ VIRTUALENV +++++++++++
# If you want to use a virtualenv, set its path on the web app setup tab.
# Then come back here and import your application object as per the
# instructions below.

# +++++++++++ WORKING DIRECTORY
# Also, if the application needs to access files for,
# say, rebuilding sources then your need to set the working directory
# accordingly on the web app setup tab.
"""

# +++++++++++ CUSTOM WSGI +++++++++++
# If you have a WSGI file that you want to serve using PythonAnywhere, perhaps
# in your home directory under version control, then use something like this:
#
import sys
path = '/home/YourSubdomain/path/to/NearlyPurePythonWebAppDemo'
if path not in sys.path:
   sys.path.append(path)

# Import the wrapped Bottle app object.
from server import app_for_wsgi_env as application


