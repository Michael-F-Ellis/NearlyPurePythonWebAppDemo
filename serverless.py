# -*- coding: utf-8 -*-
"""
A once-through script that creates and loads HTML and Javascript.
Uses Transcrypt and CPython's webbrowser module. There are 3 sections:

    Common Code -- used by both client and server
    Server Code -- Specific to the web service
    Client Code -- Compiled to JS by Transcrypt

You can search for the above names in your editor for convenient navigation.

External dependencies:
    Python >= 3.5  (Available from www.python.org)
    pip install transcrypt
    pip install htmltree

USAGE:
Typically:
    $ python serverless.py

Author: Mike Ellis
Copyright 2017 Ellis & Grant, Inc
License: MIT License

This file is part of NearlyPurePythonWebAppDemo
https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo
"""
#######################################################################
## Common Code
## Visible to CPython and Transcrypt
#######################################################################
from htmltree.htmltree import *

## If working from a renamed copy of this module, change the next
## line accordingly.
_module_basename = 'serverless'
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

    import subprocess
    import webbrowser

    def buildIndexHtml():
        """
        Create the content index.html file. For the purposes of the demo, we
        create it with an empty body element to be filled in on the client
        side.  Returns file URL.
        """
        viewport = Meta(name='viewport', content='width=device-width, initial-scale=1')

        head = Head(viewport,
                     Script(src='../__javascript__/' + _module_jsname,
                     charset='UTF-8'))

        body = Body()

        doc = Html(head, body)
        print(doc.render(0))
        return doc.renderToFile('__html__/index.html', 0)


    ## Create the HTML
    indexurl = buildIndexHtml()
    print(indexurl)

    ## Transpile to client code
    proc = subprocess.Popen('transcrypt -b -n -m {}'.format(_module_pyname), shell=True)
    if proc.wait() != 0:
        raise Exception("Failed trying to build {}".format(_module_jsname))

    ## Open in default web browser.
    webbrowser.open(indexurl)

    #__pragma__('noskip')
    ## ------------- End of Server Code -----------------------------------

    pass ## needed so the except branch looks complete to Transcrypt.
else:

    #######################################################################
    ## Client Code
    ## Compiled by Transcrypt
    #######################################################################


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



    _updater = None ## Initialized below as a generator instance.

    def start ():
        """
        Client-side app execution starts here.

        Uses JS: .getElementById, .addEventListener,
                 .textContent, .hasOwnProperty, .setInterval
        """
        ## Create the body content
        makeBody()

        ## Counter update generator ##
        def update_counter(e):
            counter = document.getElementById('counter')
            count = 0
            while True:
                count += 1
                counter.textContent = "{}".format(count)
                yield

        global _updater
        _updater = update_counter()

        ## define polling function
        def update ():
            next(_updater)

        ## First update
        update ()
        ## Repeat every second.
        window.setInterval (update, 1000)

    ## Wait until the DOM is loaded before calling start()
    document.addEventListener('DOMContentLoaded', start)

    ## ------------- End of Client Code -----------------------------------
