# -*- coding: utf-8 -*-
"""
Description: Provides a general html tree class, Element (often imported as E).

This file is part of NearlyPurePythonWebAppDemo
https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo

Compatibilty with Transcrypt Python to JS transpiler:
    By design, this module is intended for use with both CPython and
    Transcrypt.  The latter implies certain constraints on the Python
    constructs that may be used.  Compatibility with Transcrypt also requires
    the use of two __pragma__ calls to achieve compilation. These are contained
    in line comments and hence have no effect when running under CPython.

    The benefit of Transcrypt compatibility is complete freedom to use Python
    to define HTML/CSS at run time on the client side, i.e. in transpiled JS
    running in a browser.


Author: Michael Ellis
Copyright 2017 Ellis & Grant, Inc.
License: MIT License
"""
# __pragma__('kwargs')
class Element:
    """
    Generalized nested html element tree with recursive rendering

    Constructor arguments:
        tagname : valid html tag name (string)

        attrs   : attributes (dict | None)
                    keys must be valid attribute names (string)
                    values must be (string | list of strings | dict of styles)

        content : (None | string | int | float | list of (strings/ints/floats and/or elements)
                  elements must have a 'render' method that returns valid html.
                  <style> tag gets special handling. You may pass the css as a dict of
                  the form {'selector': {'property':'value', ...}, ...}

    Public Members:
        T : tagname
        A : attribute dict
        C : content

    Instance methods:
        render(indent=-1) -- defaults to no indentation, no newlines
                             indent >= 0 behaves according to the indented()
                             function in this module.

    Helper functions (defined at module level):

        indented(contentstring, indent) -- applies indentation to rendered content

        renderstyle(d) -- Special handline for inline style attributes.
                          d is a dictionary of style definitions

        renderCss(d, indent=-1) -- Special handling for <style> tag
                                   d is a dict of CSS rulesets

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

    >>> comment = E('!--', None, "This is out!")
    >>> comment.render()
    '<!-- This is out! -->'

    >>> comment.C = [body]
    >>> comment.render()
    '<!-- <body style="background-color:black;"><h1>Title</h1><br/></body> -->'

    """
    def __init__(self, tagname, attrs, content):
        ## Validate arguments
        assert isinstance(tagname, str)
        self.T = tagname.lower()
        if tagname == '!--': ## HTML comment
            attrs = None
            self.endtag = " -->"
        else:
            self.endtag = "</{}>".format(self.T)

        assert isinstance(attrs, (dict, type(None)))
        if tagname.lower() == 'style':
            assert isinstance(content, (str, dict))
        else:
            assert isinstance(content, (list, str, type(None))) ## None means an 'empty' element with no closing tag
        self.A = attrs
        self.C = content

    def render(self, indent=-1):
        """ Recursively generate html """
        rlist = []
        ## Render the tag with attributes
        opentag = "<{}".format(self.T)
        rlist.append(indented(opentag, indent))

        ## Render the attributes
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

        if self.C is None and self.T != "!--":
            ## It's a singleton tag. Close it accordingly.
            self.endtag = "/>"
            closing = self.endtag
        else:
            ## Close the tag
            if self.T == "!--":
                rlist.append(" ")
            else:
                rlist.append('>')

            ## Render the content
            if isinstance(self.C, str):
                rlist.append(indented(self.C, indent))
            elif self.T == "style":
                rlist.append(renderCss(self.C, indent))
            else:
                cindent = indent + 1 if indent >= 0 else indent
                for c in self.C:
                    if isinstance(c, (str, int, float)):
                        rlist.append(indented(c, cindent))
                    elif hasattr(c, 'render'):
                        rlist.append(c.render(cindent)) ## here's the recursion!
                    else:
                        msg="Don't know what to do with content item {}".format(c)
                        raise ValueError(msg)
            closing = indented(self.endtag, indent)
        rlist.append(closing)

        return ''.join(rlist)

def indented(contentstring, indent=-1):
    """
    Return indented content.
    indent >= 0 prefixes content with newline + 2 * indent spaces.
    indent < 0 returns content unchanged

    Docstrings:
    >>> indented("foo bar", -1)
    'foo bar'

    >>> indented("foo bar", 0)
    '\\nfoo bar'

    >>> indented("foo bar", 1)
    '\\n  foo bar'

    """
    if not indent >= 0:
        return contentstring
    else:
        return "\n{}{}".format("  " * indent, contentstring)


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

def renderCss(d, indent=-1):
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

            ruleset = " ".join([selector, '{',  renderInlineStyle(declaration), '}'])
            rulesetlist.append(indented(ruleset, indent))
        #separator = '\n' if newlines else ' '
        return ''.join(rulesetlist)

# __pragma__('nokwargs')

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
