# -*- coding: utf-8 -*-
"""
Combines contents of common.py, client.py, server.py into a single
module. There are 3 sections:

    Common Code -- used by both client and server
    Server Code -- Specific to the web service
    Client Code -- Compiled to JS by Transcrypt

You can search for the above names in your editor for convenient navigation.

External dependencies:
    Python >= 3.5  (Available from www.python.org)
    pip install transcrypt
    pip install bottlepy
    pip install htmltree

USAGE:
Typically:
    $ python minimal_allinone.py

Help is available with the -h option.

$ python minimal_allinone.py -h
usage: minimal_allinone.py [-h] [-s SERVER] [-p PORT] [--no-reloader] [--no-debug]

Nearly Pure Python Web App Demo

optional arguments:
  -h, --help            show this help message and exit
  -s SERVER, --server SERVER
                        server program to use.
  -p PORT, --port PORT  port number to serve on (default: 8800).
  --no-reloader         disable reloader (defult: enabled)
  --no-debug            disable debug mode (defult: enabled)

Author: Mike Ellis
Copyright 2017 Ellis & Grant, Inc
License: MIT License

This file is part of NearlyPurePythonWebAppDemo
https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo
"""
#######################################################################
## Common Code
## Used by both client and server
#######################################################################
from htmltree.htmltree import *

## Module globals ##
_state = {}
## If working from a renamed copy of this module, change the folowing
## line accordingly.
_module_basename = 'minimal_allinone'
_module_pyname = _module_basename + '.py'
_module_jsname = _module_basename + '.js'

## A little bit of trickiness here. We need to cause CPython to see only
## what's intended to be server-side code and Transcrypt to see only what's
## intended be client-side code. The solution is to try to invoke the Transcrypt
## pragma function.  It won't be defined in CPython, so the server code can
## go in the 'except' branch (wrapped in skip/noskip pragmas in comments)
## and the client code follows in an 'else' branch.
try:
    __pragma__('js', "")
except NameError:
    #######################################################################
    ## Server Code
    #######################################################################
    #__pragma__('skip')

    # Initialization
    import os
    import sys
    import time
    import random
    import subprocess
    import bottle
    from traceback import format_exc

    # Create an app instance.
    app = bottle.Bottle()
    request = bottle.request ## the request object accessor


    # Routes and callback functions
    # The following routes are defined below:
    #     /client.js
    #     /home (= /index.html = /)
    #     /getstate
    #     /setstepsize

    @app.route('/' + _module_jsname)
    def client():
        """
        Route for serving client js
        """
        root = os.path.abspath("./__javascript__")
        return bottle.static_file(_module_jsname, root=root)

    @app.route("/")
    @app.route("/index.html")
    @app.route("/home")
    def index():
        """ Serve the home page """
        root = os.path.abspath("./__html__")
        return bottle.static_file('index.html', root=root)

    def stategen():
        """
        In a real app, this generator would update the state at each invocation
        for transmission to clients. Here we're just incrmenting a counter.
        """
        counter = 0
        while True:
            counter += 1
            _state['count'] = counter
            yield

    ## The generator instance needs to persist outside of handlers.
    _stateg = stategen()

    @app.route("/getstate")
    def getstate():
        """
        Serve a JSON object representing state values.
        Returns: dict()
        Raises:  Nothing
        """
        next(_stateg)
        return _state


    ## Build functions

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
        index_sources = (_module_pyname,)
        target = '__html__/index.html'
        if needsBuild(target, index_sources):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'w') as f:
                print(buildIndexHtml(),file=f)

        ## build the client.js file
        client_sources = (_module_pyname,)
        if needsBuild('__javascript__/' + _module_jsname, client_sources):
            proc = subprocess.Popen('transcrypt -b -n -m {}'.format(_module_pyname), shell=True)
            if proc.wait() != 0:
                raise Exception("Failed trying to build {}".format(_module_jsname))

    def buildIndexHtml():
        """
        Create the content index.html file. For the purposes of the demo, we
        create it with an empty body element to be filled in on the client side.
        """
        viewport = Meta(name='viewport', content='width=device-width, initial-scale=1')

        head = Head(viewport,
                     Script(src='/' + _module_jsname,
                     charset='UTF-8'))

        body = Body()

        doc = Html(head, body)
        return doc.render()

    ## App service classes and functions
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

    ## Import this from external wsgi file
    app_for_wsgi_env = AppWrapperMiddleware(app)

    ## Default wrapper so we can spawn this app from commandline or
    ## from multiprocessing.
    def serve(server='wsgiref', port=8800, reloader=False, debugmode=False):
        """
        Build the html and js files, if needed, then launch the app.

        The default server is the single-threaded 'wsgiref' server that comes with
        Python. It's fine for a demo, but for production you'll want to use
        something better, e.g. server='cherrypy'. For an extensive list of server
        options, see http://bottlepy.org/docs/dev/deployment.html
        """
        bottle.debug(debugmode)

        ## Client side tracks _state['server_start_time']
        ## to decide if it should reload.
        _state['server_start_time'] = time.time()

        ## rebuild as needed
        doBuild()

        ## Launch the web service loop.
        bottle.run(app,
                   host='0.0.0.0',
                   server=server,
                   port=port,
                   reloader=reloader,
                   debug=debugmode)

    ## The following runs only when we start from
    ## the command line.
    if __name__ == '__main__':
        import argparse
        parser = argparse.ArgumentParser(
                  description = "My Web App")
        parser.add_argument('-s', '--server', type=str, default='wsgiref',
                            help="server program to use.")
        parser.add_argument('-p', '--port', type=int, default=8800,
                            help="port number to serve on. (8800)")
        parser.add_argument('--no-reloader', dest='reloader', action='store_false',
                            help="disable reloader (defult: enabled)")
        parser.add_argument('--no-debug', dest='debug', action='store_false',
                            help="disable debug mode (defult: enabled)")
        parser.set_defaults(reloader=True)
        parser.set_defaults(debug=True)
        args = parser.parse_args()
        serve(server=args.server, port=args.port,
              reloader=args.reloader, debugmode=args.debug)

    #__pragma__('noskip')
    ## ------------- End of Server Code -----------------------------------

    pass ## needed so the except branch looks complete to Transcrypt.
else:

    #######################################################################
    ## Client Code
    ## Compiled by Transcrypt
    #######################################################################

    _prior_state = {}
    _readouts = None

    def makeBody():
        """
        Create HTML for the body element content. This is done as a demo to show
        that the code in htmltree.py works in Transcrypted JS as well as in Python.
        It could have been accomplished just as easily on the server side.

        Uses JS: .innerHTML, .style
        """
        document.body.style.backgroundColor = "black"
        banner = H1("Hello, {}.".format(_module_basename), style=dict(color='yellow'))
        counter = H2(id="counter", style=dict(color='green'))
        header = Div(banner, counter, style=dict(text_align='center'))
        bodycontent = Div(header)

        ## Use the DOM API to insert rendered content
        document.body.innerHTML = bodycontent.render()

    # jQuery replacement functions
    # The next 3 functions provide some replacements for frequently used
    # jQquery methods. They could logically be placed in a separate module.
    def triggerCustomEvent(name, data):
        """
        JS version of jQuery.trigger.
        see  http://youmightnotneedjquery.com/#trigger_custom

        Uses JS: CustomEvent, .createEvent, .dispatchEvent
        """
        if window.CustomEvent:
            event = __new__ (CustomEvent(name, {'detail' : data}))
        else:
            event = document.createEvent('CustomEvent')
            event.initCustomEvent(name, True, True, data)
        document.dispatchEvent(event)

    def getJSON(url, f):
        """
        JS version of jQuery.getJSON
        see http://youmightnotneedjquery.com/#get_json
        url must return a JSON string
        f(data) handles an object parsed from the return JSON string

        Uses JS: XMLHttpRequest, JSON.parse
        """
        request = __new__ (XMLHttpRequest())
        request.open('GET', url, True)
        def onload():
            if 200 <= request.status < 400:
                data = JSON.parse(request.responseText)
                f(data) ## call handler with object created from JSON string
            else:
                _ = "Server returned {} for getJSON request on {}".format(request.status, url)
                console.log(_)
        def onerror():
            _ = "Connection error for getJSON request on {}".format(url)
            console.log(_)
        request.onload = onload
        request.onerror = onerror
        request.send()

    def post(url, data):
        """
        JS version of jQuery.post
        see http://youmightnotneedjquery.com/#post
        data is expected to be a dict.

        Uses JS: XMLHttpRequest, .hasOwnProperty, encodeURIComponent
        """
        request = __new__(XMLHttpRequest())
        request.open('POST', url, True)
        request.setRequestHeader('Content-Type',
                                 'application/x-www-form-urlencoded; '
                                 'charset=UTF-8')
        ## serialize the data, see http://stackoverflow.com/a/1714899/426853
        ldata = []
        for k,v in data.items():
            if data.hasOwnProperty(k):
                lh = encodeURIComponent(k)
                rh = encodeURIComponent(v)
                ldata.append("{}={}".format(lh, rh))

        request.send("&".join(ldata))

    ## End of jQuery replacement functions ##

    ## Application callbacks ##
    def getState():
        """ Fetch JSON obj containing monitored variables. """
        def f(data):
            global _state, _prior_state
            _prior_state.update(_state)
            _state = data
            triggerCustomEvent('state:update', {})
            #console.log(_state)
        getJSON('/getstate', f)
        return


    def start ():
        """
        Client-side app execution starts here.

        Uses JS: .getElementById, .addEventListener,
                 .hasOwnProperty, location, .setInterval
        """
        ## Create the body content
        makeBody()

        ## Bind event handlers ##
        counter = document.getElementById('counter')

        def update_counter(e):
            counter.textContent = "{}".format(_state['count'])

        document.addEventListener('state:update', update_counter)

        ## define polling function
        global _state, _prior_state
        def update ():
            getState()
            ## Reload if server has restarted
            if (_prior_state is not None and
                _prior_state.hasOwnProperty('server_start_time')):
                if _state['server_start_time'] > _prior_state['server_start_time']:
                    location.reload(True)

        ## First update
        update ()
        ## Repeat every second.
        window.setInterval (update, 1000)

    ## Wait until the DOM is loaded before calling start()
    document.addEventListener('DOMContentLoaded', start)

    ## ------------- End of Client Code -----------------------------------
