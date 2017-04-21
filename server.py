#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Description: Server for NearlyPurePythonWebAppDemo.

Sources and more info at:
https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo

Author: Mike Ellis
Copyright 2017 Ellis & Grant, Inc
License: MIT License
"""


############################################################
# Initialization
############################################################
import os
import sys
import time
import doctest
import random
import subprocess
import bottle
import common
from traceback import format_exc
from htmltree import Element as E

import client
# Create an app instance.
app = bottle.Bottle()
request = bottle.request ## the request object accessor


############################################################
# Build index.html
############################################################
def buildIndexHtml():
    """
    Create the content index.html file. For the purposes of the demo, we
    create it with an empty body element to be filled in on the client side.
    Returns: None
    Raises:  Nothing
    """

    linkcolors = list(zip('link visited hover active'.split(),
                          'red green hotpink blue'.split(),))
    linkcss = '\n'.join(['a:{} {{color: {};}}'.format(s,c) for s,c in linkcolors])

    head = E('head', None,
             [
              E('style', None, linkcss),
              E('script', {'src':'/client.js', 'charset':'UTF-8'}, []),
             ])

    body = E('body', {'style':{'background-color':'black'}},
             "Replace me on the client side.")

    doc = E('html', None,[head, body])
    return doc.render()


############################################################
# Routes and callback functions
# The following routes are defined below:
#     /client.js
#     /home (= /index.html = /)
#     /getstate
#     /setstepsize
############################################################

@app.route('/client.js')
def client():
    """
    Route for serving client.js
    """
    root = os.path.abspath("./__javascript__")
    return bottle.static_file('client.js', root=root)

@app.route("/")
@app.route("/index.html")
@app.route("/home")
def index():
    """ Serve the home page """
    root = os.path.abspath("./__html__")
    return bottle.static_file('index.html', root=root)

## Module level variable used to exchange data beteen handlers
_state = {}

def stategen():
    """
    Initialize each state item with a random float between 0 and 10, then
    on each next() call, 'walk' the value by a randomly chosen increment. The
    purpose is to simulate a set of drifting measurements to be displayed
    and color coded on the client side.
    """
    last = time.time()
    counter = 0
    nitems = common.nitems
    statekeys = common.statekeys
    _state['step'] = (-common.stepsize, 0.0, common.stepsize)
    _state['stepsize'] = common.stepsize
    statevalues = [round(random.random()*10, 2) for n in range(nitems)]
    _state.update(dict(zip(statekeys, statevalues)))
    while True:
        ## Update no more frequently than twice per second
        now = time.time()
        if now - last >= 0.5:
            last = now
            counter += 1
            step = _state['step']
            statevalues = [round(v + random.choice(step), 2) for v in statevalues]
            statevalues = [min(10.0, max(0.0, v)) for v in statevalues]
            _state.update(dict(zip(statekeys, statevalues)))
            _state['count'] = counter
        yield

## The generator needs to persist outside of handlers.
_stateg = stategen()

@app.route("/getstate")
def getstate():
    """
    Serve a JSON object representing state values.
    Returns: dict(count=n, item0=v0, item1=v1, ...)
    Raises:  Nothing
    """
    next(_stateg)
    return _state

@app.post("/setstepsize")
def setStepSize():
    """
    Called when user submits step size input. Validation
    happens client side so we don't check it here. In a real
    app you'd want some server-side validation would help protect
    against exploits.
    """
    stepsize = float(request.forms.get('stepsize'))
    _state['stepsize'] = stepsize
    _state['step'] = (-stepsize, 0, stepsize)
    return {}

########################################################
# Build functions
########################################################

def needsBuild(target, sources):
    """
    Returns True if target doesn't exist or is older than any of the sources.
    Sources must be an iterable, e.g. list or tuple.
    """
    return not os.path.exists(target) or any([(os.stat(target).st_mtime
              < os.stat(source).st_mtime) for source in sources])
def doBuild():
    """
    Build the html and js files, if needed.

    Note: In larger projects with more complex dependencies, you'll probably
    want to use make or scons to build the targets instead of the simple
    approach taken here.
    """
    ## build the index.html file
    index_sources = ('server.py', 'htmltree.py', 'common.py')
    target = '__html__/index.html'
    if needsBuild(target, index_sources):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, 'w') as f:
            print(buildIndexHtml(),file=f)

    ## build the client.js file
    client_sources = ('client.py', 'htmltree.py', 'common.py')
    if needsBuild('__javascript__/client.js', client_sources):
        proc = subprocess.Popen('transcrypt -b -n -m client.py', shell=True)
        if proc.wait() != 0:
            raise Exception("Failed trying to build client.js")

class AppWrapperMiddleware:
    """
    Some hosted environments, e.g. pythonanywhere.com, require you
    to export the Bottle app object. Exporting an instance of this
    wrapper class makes sure the build procedure runs on startup.
    """
    def __init__(self, app):
      self.app = app
    def __call__(self, e, h):
      doBuild()
      return self.app(e,h)

##################################################
## Import this from external wsgi file
app_for_wsgi_env = AppWrapperMiddleware(app)
##################################################

########################################################
## Default wrapper  so we can spawn this app  commandline or
## from multiprocessing.
########################################################
def serve(server='wsgiref', port=8800, reloader=False):
    """
    Build the html and js files, if needed, then launch the app.

    The default server is the single-threaded 'wsgiref' server that comes with
    Python. It's fine for a demo, but for production you'll want to use
    something better, e.g. server='cherrypy'. For an extensive list of server
    options, see http://bottlepy.org/docs/dev/deployment.html
    """
    bottle.debug(True) ## TODO remove this from production version.
    ## gets updated on each auto-reaload. Client side tracks this
    ## to decide if it should reload.
    _state['server_start_time'] = time.time()
    doBuild()

    ## Launch the web service loop.
    bottle.run(app,
               host='0.0.0.0',
               server=server,
               port=port,
               reloader=reloader,
               debug=True)

###################################################
## The following runs only when we start from
## the command line.
###################################################
if __name__ == '__main__':
    doctest.testmod()
    import argparse
    parser = argparse.ArgumentParser(
              description = "Nearly Pure Python Web App Demo")
    parser.add_argument('-s', '--server', type=str, default='wsgiref', help="server program to use.")
    parser.add_argument('-p', '--port', type=int, default=8800, help="port number to serve on.")
    parser.add_argument('--no-reloader', dest='reloader', action='store_true', help="disable reloader (defult: enabled)")
    parser.set_defaults(reloader=True)
    args = parser.parse_args()
    serve(server=args.server, port=args.port, reloader=args.reloader)

