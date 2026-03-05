.. _how to write tutorials:

Documentation for writing tutorials
===================================

It is recommended for contributors to add or update tutorials to describe new changes or better explain existing features of ``qnngds``.

In order to write a tutorial, a small set of scripts has been provided that provides a limited `literate programming <https://en.wikipedia.org/wiki/Literate_programming>`_ functionality.
In this way, your tutorial code can be written as a runnable file which is useful for performing unit tests to verify that the tutorial is up to date with any changes made to ``qnngds``.

See the existing tutorials in ``docs/src/tutorials/`` for examples.
Any line that starts with a comment will be added to the reStructured text output, and the rest is treated like code.

There are three special comments, ``## IMAGE``, ``## IMAGE_ZOOM``, and ``## STOP``, which can be used to output a quickplot image (and zoomed copy), and tell the parser to stop emitting code/reStructured text.

The parser is located in ``docs/src/generate_tutorials.py``, and plot generation is done with ``save_qp``, defined in ``docs/src/tutorials/_save_qp.py``.
