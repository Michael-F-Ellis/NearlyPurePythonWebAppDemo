# -*- coding: utf-8 -*-
"""
Description: Provides a general html tree class, Element (often imported as E).

This file is part of NearlyPurePythonWebAppDemo
https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo

Author: Michael Ellis
Copyright 2017 Ellis & Grant, Inc.
License: MIT License
"""
class Element:
    """
    Generalized nested html element with recursive rendering

    Constructor arguments:
        tagname : valid html tag name (string)
        attrs   : attributes (dict | None)
                    keys must be valid attribute names (string)
                    values must be (string | list of strings | dict of styles)
        content : (None | string | list of (strings and/or elements)
                    elements must have a 'render' method that returns valid html.
                  <style> tag gets special handling. You may pass the css as a dict of
                  the form {'selector': {'property':'value', ...}, ...}

    Instance methods:
        render()

    Static methods:
        renderstyle(d) -- moved to module level until Transcrypt supports
                       -- method decorators.

    Public Members:
        T : tagname
        A : attribute dict
        C : content

    Doctests:
    >>> E = Element
    >>> doc = E('html', None, [])
    >>> doc.render()
    '<html></html>'
    >>> doc.C.append(E('head', None, []))
    >>> doc.render()
    '<html><head></head></html>'
    >>> body = E('body', {'style':{'background-color':'black'}}, [E('h1', None, "Title")])
    >>> body.C.append(E('br', None, None))
    >>> body.render()
    '<body style="background-color:black;"><h1>Title</h1><br/></body>'
    >>> doc.C.append(body)
    >>> doc.render()
    '<html><head></head><body style="background-color:black;"><h1>Title</h1><br/></body></html>'

    >>> style = E('style', None, {'p.myclass': {'margin': '4px', 'font-color': 'blue'}})
    >>> style.render()
    '<style>p.myclass { margin:4px; font-color:blue; }</style>'
    """
    def __init__(self, tagname, attrs, content):
        ## Validate arguments
        assert isinstance(tagname, str)
        if tagname == '!--':
            raise ValueError("Sorry, can't handle html comments yet.")
        assert isinstance(attrs, (dict, type(None)))
        if tagname.lower() == 'style':
            assert isinstance(content, (str, dict))
        else:
            assert isinstance(content, (list, str, type(None))) ## None means an 'empty' element with no closing tag
        self.T = tagname.lower()
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
                elif v is None:
                    rlist.append(' {}'.format(a)) # bare attribute, e.g. 'disabled'
                elif isinstance(v,list):
                    _ = ' '.join(v)     ## must be list of strings
                    rlist.append(' {}="{}"'.format(a, _))
                elif isinstance(v,dict) and a=='style':
                    rlist.append(' {}="{}"'.format(a,renderInlineStyle(v)))
                else:
                    msg="Don't know what to with {}={}".format(a,v)
                    raise ValueError(msg)

        if self.C is None:
            ## It's a singleton tag. Close it accordingly.
            rlist.append("/>")
            needs_end_tag = False
        else:
            ## Close the tag normally
            rlist.append('>')
            needs_end_tag = True

            ## render the content
            if isinstance(self.C, str):
                rlist.append(self.C)
            elif self.T == "style":
                rlist.append(renderCss(self.C))
            else:
                for c in self.C:
                    if isinstance(c, str):
                        rlist.append(c)
                    elif isinstance(c, (int, float)):
                        rlist.append(str(c))
                    elif hasattr(c, 'render'):
                        rlist.append(c.render()) ## here's the recursion!
                    else:
                        msg="Don't know what to do with content item {}".format(c)
                        raise ValueError(msg)

        if needs_end_tag:
            rlist.append('</{}>'.format(self.T))

        return ''.join(rlist)

def renderInlineStyle(d):
    """If d is a dict of styles, return a proper style string """
    if isinstance(d, dict):
        style=[]
        for k,v in d.items():
            ## for convenience, convert underscores in keys to hyphens
            kh = k.replace('_', '-')
            style.append("{}:{};".format(kh, v))
        separator = ' '
        result = separator.join(style)
    elif isinstance(d, str):
        result = d
    else:
        msg = "Cannot convert {} to style string".format(d)
        raise TypeError(msg)
    return result

def renderCss(d, newlines=True):
    """ If d is a dict of rulesets, render a string of CSS rulesets """
    if not isinstance(d, dict):
        msg = "Expected dictionary of CSS rulesets, got {}.".format(d)
        raise TypeError(msg)
    else:
        rulesetlist = []
        for selector, declaration in d.items():
            #print("In renderCss with selector = {}".format(selector))
            if not isinstance(selector, str):
                msg = "Expected selector string, got {}".format(selector)
                raise TypeError(msg)

            ruleset = [selector, '{',  renderInlineStyle(declaration), '}']
            rulesetlist.append(" ".join(ruleset))
        separator = '\n' if newlines else ' '
        return separator.join(rulesetlist)

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
