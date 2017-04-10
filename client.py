__pragma__ ('alias', 'jq', '$')

from htmltree import E

_state = None
_jq_readouts = None
#E = htmltree.E
_test = E('div', {'style':{'background-color':'orange'}},[])
console.log(_test.render())

def getState():
    """ Fetch JSON obj containing label text """
    def f(data):
        global _state
        _state = data
        jq(document).trigger('state:update')
        #console.log(_state)
    jq.getJSON('/getstate', f)
    return

def update_readouts():
    """
    Triggered on each readout by 'state:update' custom event.
    """
    #console.log("Enter update_readouts")
    ## queue the new values and colora
    queue = []
    for el in _jq_readouts:
        #console.log(el)
        jq_el = jq(el)
        key = jq_el.attr('data-key')
        value = _state[key]
        valuef = float(value)
        if valuef <= 2.0:
            color = 'blue'
        elif valuef >= 8.0:
            color = 'red'
        else:
            color = 'green'
        queue.append((jq_el, value, color))

    ## write them to the DOM
    for jq_el, value, color in queue:
        jq_el.text(value).attr('style', "color:{}; font-size:32;".format(color))


def start ():
    global _jq_readouts
    _jq_readouts = jq('.readout')
    jq('.readout').css("font-size:12;")
    jq(document).on('state:update', update_readouts)
    def update ():
        getState()

    update ()
    window.setInterval (update, 500)

