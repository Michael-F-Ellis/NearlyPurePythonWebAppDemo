# Auto Reload

Other things being equal, the rate of progress in application development is directly related to the time it takes to make and test one small change. By default, the NearlyPurePythonWebAppDemo (NPPWAD hereafter) skeleton will detect changes in any of the Python source files and reload both the server and the client side -- including a rebuild of `client.js` from `client.py` if needed.


## How it works

Bottle already provides an auto-reloader and a debug mode. The Bottle Tutorial explains both of those [here](https://bottlepy.org/docs/dev/tutorial.html#debug-mode). NPPWAD takes advantage of them and extends them by

1. Incorporating a simple rebuild facility in `server.py,` and
2. Running a client-side check on server start time in `client.py`.

The result is that changing any of the .py source files triggers the following chain of events:

* Bottle notices that a file has changed and reloads `server.py.`
* As `server.py` re-initializes it checks the modification times on the sources and regenerates `__html__/index.html` and `client.js` as needed.
* If a prior version of `client.js` is running in a browser, the next state update will detect a change in `_state['server_start_time']` and reload the page using `location.reload()`.

## Usage
Reload and debug are enabled by default when you launch from the command line.

To disable these features in a production version, launch `server.py` with `--no-reloader --no-debug` at the command line. If launching by direct call to `server.serve()`, note that reload and debug are *disabled* by default in the keyword args to `serve()`.



## Limitations and caveats

The reloader in Bottle inspects `sys.modules` to determine what files to monitor -- meaning that it only tracks modules that are in the tree of modules imported into `server.py.` To monitor changes in client-side Python sources, e.g. `client.py`, we must import them into `server.py` -- which means that such modules must not cause errors or have undesired side effects when imported into Python code. Notice, for example, at the bottom of `client.py` the lines

```
try:
    document.addEventListener('DOMContentLoaded', start)
except NameError:
    pass
```
This prevents a failed import when `document`, a global object in JS, is not defined in Python. Fortunately, the event-driven nature of client-side code makes it easy to confine module-level execution to a single statement, as above, to avoid littering the code with many similar guard constructs.

Another obvious limitation is that the reloader only monitors Python sources. For a large project with sources in other languages, you would probably want to set up a build system triggered from a monitor program such as `entr`.  To connect it with the `server.py` reloader, you could arrange for the build system to update a dummy python module, e.g. `reloadme.py` imported by `server.py` for the sole purpose of detecting the need for a reload.








