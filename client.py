
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
__pragma__ ('alias', 'jq', '$')

import common
from htmltree import Element as E

_state = None
_jq_readouts = None

def makeBody():
    """
    Create HTML for the body element content. This is done as a demo to show
    that the code in htmltree.py works in Transcrypted JS as well as in Python.
    It could have been accomplished just as easily on the server side.
    """
    title = E('h1', {'style':{'color':'yellow',}}, "Nearly Pure Python Web App Demo")
    projectlink =  E('a',
                      {'href':'https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo'},
                      'Source code on GitHub')
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

def getState():
    """ Fetch JSON obj containing monitored variables. """
    def f(data):
        global _state
        _state = data
        jq(document).trigger('state:update')
        #console.log(_state)
    jq.getJSON('/getstate', f)
    return

def update_readouts():
    """
    Triggered on each readout by 'state:update' custom event. We check each
    state value and alter it's text color accordingly.
    """
    ## queue the new values and colora
    queue = []
    for el in _jq_readouts:
        jq_el = jq(el)
        key = jq_el.attr('data-key')
        value = _state[key]
        valuef = float(value)
        if valuef <= 2.0:
            color = 'deepskyblue'
        elif valuef >= 8.0:
            color = 'red'
        else:
            color = 'green'
        queue.append((jq_el, value, color))

    ## write them to the DOM
    for jq_el, value, color in queue:
        jq_el.text(value).attr('style', "color:{}; font-size:32;".format(color))

    ## Also update the stepsize input with the current value
    jq('#stepsize').val(_state['stepsize'])


def handle_stepchange(event):
    """
    Check that the request for a new step size is a number between 0 and 10
    before allowing the submit action to proceed.
    """
    fail_msg = "Step size must be a number between 0 and 10"
    v = jq('#stepinput').val()
    # Transcrypt float() is buggy, so use some inline JS.
    # See https://github.com/QQuick/Transcrypt/issues/314
    #__pragma__('js','{}','var vj = parseFloat(v); var isfloat = !isNaN(vj);')
    if isfloat and (0.0 <= vj <= 10.0):
        ## It's valid. Send it.
        jq.post('/setstepsize', { 'stepsize': v })
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
    global _jq_readouts
    _jq_readouts = jq('.readout')
    jq('.readout').css("font-size:12;")

    ## Bind event handler to step change form
    jq('#setstep').submit(handle_stepchange)

    ## Bind custom event handler to document
    jq(document).on('state:update', update_readouts)

    ## define polling function
    def update ():
        getState()

    ## First update
    update ()
    ## Repeat every 0.5 secondss
    window.setInterval (update, 500)

