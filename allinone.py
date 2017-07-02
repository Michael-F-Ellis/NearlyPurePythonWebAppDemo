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
    $ python allinone.py

Help is available with the -h option.

$ python allinone.py -h
usage: allinone.py [-h] [-s SERVER] [-p PORT] [--no-reloader] [--no-debug]

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
class Common():
    def __init__(self, nitems, stepsize):
        ## The number of state items to display in the web page.
        self.nitems = nitems
        ## Step size for the simulation
        self.stepsize = stepsize
        ## Id strings for readouts
        self.statekeys =  ["item{}".format(n) for n in range(nitems)]

common = Common(10, 0.5)

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

    ## We import client.py so the Bottle reloader will track it for changes
    ## It has no use in this module and no side effects other than a small
    ## overhead to load it.
    import client

    # Create an app instance.
    app = bottle.Bottle()
    request = bottle.request ## the request object accessor


    # Routes and callback functions
    # The following routes are defined below:
    #     /client.js
    #     /home (= /index.html = /)
    #     /getstate
    #     /setstepsize

    @app.route('/allinone.js')
    def client():
        """
        Route for serving client.js
        """
        root = os.path.abspath("./__javascript__")
        return bottle.static_file('allinone.js', root=root)

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

    # Build functions

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
        index_sources = ('allinone.py',)
        target = '__html__/index.html'
        if needsBuild(target, index_sources):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'w') as f:
                print(buildIndexHtml(),file=f)

        ## build the client.js file
        client_sources = ('allinone.py',)
        if needsBuild('__javascript__/allinone.js', client_sources):
            proc = subprocess.Popen('transcrypt -b -n -m allinone.py', shell=True)
            if proc.wait() != 0:
                raise Exception("Failed trying to build allinone.js")

    def buildIndexHtml():
        """
        Create the content index.html file. For the purposes of the demo, we
        create it with an empty body element to be filled in on the client side.
        """

        style = Style(**{'a:link':dict(color='red'),
                         'a:visited':dict(color='green'),
                         'a:hover':dict(color='hotpink'),
                         'a:active':dict(color='blue'),
                         })

        head = Head(style, Script(src='/allinone.js', charset='UTF-8'))

        body = Body("Replace me on the client side",
                    style=dict(background_color='black'))

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

    ## Default wrapper  so we can spawn this app from commandline or
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
                  description = "Nearly Pure Python Web App Demo")
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
    ## Compiled by Transcrypt as 'allinone.js'
    #######################################################################

    _state = {}
    _prior_state = {}
    _readouts = None

    def makeBody():
        """
        Create HTML for the body element content. This is done as a demo to show
        that the code in htmltree.py works in Transcrypted JS as well as in Python.
        It could have been accomplished just as easily on the server side.

        Uses JS: .innerHTML
        """
        banner = H1("Nearly Pure Python Web App Demo", style=dict(color='yellow'))
        projectlink = A('Source Code on GitHub',
                        href='https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo')
        subbanner = H2(projectlink)

        header = Div(banner, subbanner, style=dict(text_align='center'))

        readouts = []
        for datakey in common.statekeys:
            readouts.append(Div('waiting ...', _class='readout', data_key=datakey))

        stepinput = Label("Step Size",
                      Input(id='stepinput', type='text', style=dict(margin='1em')),
                    style=dict(color='white'))

        stepsubmit = Input(type="submit", value="Submit")

        stepform = Form(
                     Div(stepinput, stepsubmit, style=dict(margin='20px')),
                   id='setstep')

        bodycontent = Div(header)
        bodycontent.C.extend(readouts)
        bodycontent.C.append(stepform)

        ## Use the DOM API to insert rendered content
        console.log(bodycontent.render())
        document.body.innerHTML = bodycontent.render()

    # jQuery replacement functions
    # The next 3 functions could logically be placed in a
    # separate module.
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

    # End of j!uery replacement functions

    ## Application callbacks
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

    def update_readouts():
        """
        Triggered on each readout by 'state:update' custom event. We check each
        state value and alter it's text color accordingly.

        Uses JS: .getAttribute, .textContent, .setAttribute, .getElementById,
                 .activeElement
        """
        ## queue the new values and colora
        queue = []
        for el in _readouts:
            key = el.getAttribute('data-key')
            value = _state[key]
            valuef = float(value)
            if valuef <= 2.0:
                color = 'deepskyblue'
            elif valuef >= 8.0:
                color = 'red'
            else:
                color = 'green'
            queue.append((el, value, color))

        ## write them to the DOM
        for el, value, color in queue:
            el.textContent = value
            el.setAttribute('style', "color:{}; font-size:32;".format(color))

        ## Also update the stepsize input with the current value, but
        ## check that the element does not have focus before doing so
        ## tp prevent update while user is typing.
        inp = document.getElementById('stepinput')
        if inp != document.activeElement:
            inp.value = _state['stepsize']


    def handle_stepchange(event):
        """
        Check that the request for a new step size is a number between 0 and 10
        before allowing the submit action to proceed.

        Uses JS: .getElementById, alert, parseFloat, isNaN
        """
        fail_msg = "Step size must be a number between 0 and 10"
        v = document.getElementById('stepinput').value
        # Transcrypt float() is buggy, so use some inline JS.
        # See https://github.com/QQuick/Transcrypt/issues/314
        #__pragma__('js','{}','var vj = parseFloat(v); var isfloat = !isNaN(vj);')
        if isfloat and (0.0 <= vj <= 10.0):
            ## It's valid. Send it.
            post('/setstepsize', { 'stepsize': v })
            return False
        else:
            alert(fail_msg)
            return False

    def start ():
        """
        Client-side app execution starts here.

        Uses JS: .querySelectorAll, .style, .getElementById, .addEventListener,
                 .hasOwnProperty, location, .setInterval
        """
        ## Create the body content
        makeBody()

        ## Initialize the readouts
        global _readouts
        _readouts = document.querySelectorAll('.readout')
        for el in _readouts:
            el.style.fontSize = '12'


        ## Bind event handler to step change form
        ssform = document.getElementById('setstep')
        ssform.addEventListener('submit', handle_stepchange)

        ## Bind custom event handler to document
        document.addEventListener('state:update', update_readouts)

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
        ## Repeat every 0.5 secondss
        window.setInterval (update, 500)

    ## Wait until the DOM is loaded before calling start()
    document.addEventListener('DOMContentLoaded', start)

    ## ------------- End of Client Code -----------------------------------
