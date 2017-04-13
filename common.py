# -*- coding: utf-8 -*-
"""
Description: Information needed on both client and server side.

This file is part of NearlyPurePythonWebAppDemo
https://github.com/Michael-F-Ellis/NearlyPurePythonWebAppDemo

Author: Mike Ellis
Copyright 2017 Ellis & Grant, Inc.
License: MIT License
"""
## The number of state items to display in the web page.
nitems = 10
## Enumerated names for each item.
statekeys = ["item{}".format(n) for n in range(nitems)]
## Initial step size for random walk
stepsize = 0.5
