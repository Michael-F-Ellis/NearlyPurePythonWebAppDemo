# -*- coding: utf-8 -*-
"""
Description: Provides a general html tree class, E.
Author: Michael Ellis
Copyright 2017 Ellis & Grant, Inc.
"""
class E:
    """
    Generalized nested html element with recursive rendering

    Constructor arguments:
        tagname : valid html tag name (string)
        attrs   : attributes (dict | None)
                    keys must be valid attribute names (string)
                    values must be (string | list of strings | dict of styles)
        content : (None | string | list of (strings and/or elements)
                    elements must have a 'render' method that returns valid html.

    Instance methods:
        render()

    Static methods:
        renderstyle(d)

    Public Members:
        T : tagname
        A : attribute dict
        C : content

    Doctests:
    >>> doc = E('html', None, [])
    >>> doc.render()
    '<html></html>'
    >>> doc.C.append(E('head', None, []))
    >>> doc.render()
    '<html><head></head></html>'
    >>> body = E('body', {'style':{'background-color':'black'}}, [E('h1', None, "Title")])
    >>> body.render()
    '<body style="background-color:black;"><h1>Title</h1></body>'
    >>> doc.C.append(body)
    >>> doc.render()
    '<html><head></head><body style="background-color:black;"><h1>Title</h1></body></html>'

    """
    def __init__(self, tagname, attrs, content):
        ## Validate arguments
        assert isinstance(tagname, str)
        assert isinstance(attrs, (dict, type(None)))
        assert isinstance(content, (list, str, type(None))) ## None means an 'empty' element with no closing tag
        self.T = tagname
        self.A = attrs
        self.C = content

    def render(self):
        """ Recursively generate html """
        rlist = []
        ## Render the tag with attributes
        rlist.append("<{}".format(self.T))
        if self.A is not None:
            for a, v in self.A.items():
                a = a.replace('_', '-') ## replace underscores with hyphens
                if isinstance(v, str):
                    rlist.append(' {}="{}"'.format(a,v))
                elif isinstance(v,list):
                    _ = ' '.join(v)     ## must be list of strings
                    rlist.append(' {}="{}"'.format(a, _))
                elif isinstance(v,dict) and a=='style':
                    rlist.append(' {}="{}"'.format(a,renderstyle(v)))
                else:
                    msg="Don't know what to with {}={}".format(a,v)
                    raise ValueError(msg)

        if self.C is None:
            ## It's a singleton tag. Close it accordingly.
            rlist.append("/>\n")
        else:
            ## Close the tag normally
            rlist.append('>')
            ## render the content
            for c in self.C:
                if hasattr(c, 'render'):
                    rlist.append(c.render())
                elif isinstance(c, str):
                    rlist.append(c)
                else:
                    msg="Don't know what to do with content item {}".format(c)
                    raise ValueError(msg)
            ## Add closing tag
            rlist.append('</{}>'.format(self.T))
        return ''.join(rlist)

def renderstyle(d):
    """If d is a dict of styles, return a proper style string """
    if isinstance(d, dict):
        style=[]
        for k,v in d.items():
            ## for convenience, convert underscores in keys to hyphens
            kh = k.replace('_', '-')
            style.append("{}:{};".format(kh, v))
        result = ' '.join(style)
    elif isinstance(d, str):
        result = d
    else:
        msg = "Cannot convert {} to style string".format(d)
        raise TypeError(msg)
    return result


## The 'skip' pragma tells the Transcrypt Python to JS transpiler to
## ignore a section of code. It's needed here because the 'run as script'
## idiom causes an error in Transcrypt and has no meaning in that context.
## Putting the pragmas in comments means they'll be ignored and cause no
## problems in a real python interpreter.

# __pragma__ ('skip')
if __name__ == '__main__':
    import doctest
    doctest.testmod()
# __pragma__ ('noskip')
