
# -*- coding: utf-8 -*-
"""
Description: Client-side code that gets transpiled to JS by Transcrypt(TM)
Execution begins in the start() method -- which is invoked from a script element
in the html head element of index.html

This file is part of NearlyPurePythonWebAppDemo
https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo

Author: Mike Ellis
Copyright 2017 Ellis & Grant, Inc.
License: MIT License
"""

import common
from htmltree import Element as E

_state = None
_readouts = None

def makeBody():
    """
    Create HTML for the body element content. This is done as a demo to show
    that the code in htmltree.py works in Transcrypted JS as well as in Python.
    It could have been accomplished just as easily on the server side.
    """
    title = E('h1', {'style':{'color':'yellow',}}, "Nearly Pure Python Web App Demo")
    projectlink =  E('a',
                      {'href':'https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo'},
                      'Source Code on GitHub')
    subtitle = E('h2', None, [projectlink])
    header = E('div', {'style':{'text-align':'center'}}, [title, subtitle])

    readouts = []
    for datakey in common.statekeys:
        readouts.append(E('div', {'class':'readout', 'data-key':datakey}, 'waiting ...'))

    stepinput = E('label', {'style':{'color':'white'}},
            ["Step Size", E('input', {'id':'stepinput', 'type':'text','style':{'margin':'1em'}}, None)])
    stepsubmit = E('input', {'type':'submit'}, None)
    stepform = E('form', {'id':'setstep',},
            [E('div',{'style':{'margin':'20px'}},[stepinput, stepsubmit])])

    bodycontent = E('div', None, [header])
    bodycontent.C.extend(readouts)
    bodycontent.C.append(stepform)

    ## Use the DOM API to insert rendered content
    document.body.innerHTML = bodycontent.render()

#########################################################
# jQuery replacement functions
# The next 3 function could logically be placed in a
# separate module.
#########################################################
def triggerCustomEvent(name, data):
    """
    JS version of jQuery.trigger.
    see  http://youmightnotneedjquery.com/#trigger_custom
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
########################################################

def getState():
    """ Fetch JSON obj containing monitored variables. """
    def f(data):
        global _state
        _state = data
        triggerCustomEvent('state:update', {})
        #console.log(_state)
    getJSON('/getstate', f)
    return

def update_readouts():
    """
    Triggered on each readout by 'state:update' custom event. We check each
    state value and alter it's text color accordingly.
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
    """
    ## Create the body content
    makeBody()

    ## Initialize the readouts
    nonlocal _readouts
    _readouts = document.querySelectorAll('.readout')
    for el in _readouts:
        el.style.fontSize = '12'


    ## Bind event handler to step change form
    ssform = document.getElementById('setstep')
    ssform.addEventListener('submit', handle_stepchange)

    ## Bind custom event handler to document
    document.addEventListener('state:update', update_readouts)

    ## define polling function
    def update ():
        getState()

    ## First update
    update ()
    ## Repeat every 0.5 secondss
    window.setInterval (update, 500)

document.addEventListener('DOMContentLoaded', start)
