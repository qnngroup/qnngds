.. _experiment_generate_beginner3
Keepout regions for positive-tone ebeam layouts with ``experiment.generate``
============================================================================

Now, we will demonstrate how to do keepouts with an additional keepout layer.

Imports are the same as in :ref:`experiment_generate_beginner1`:

.. literalinclude:: experiment_generate_beginner3.py
   :language: python
   :linenos:
   :lines: 1-3

When setting up the PDK, we'll define four layers this time, as well as a new interlayer transition between
the two ebeam layers using ``geometries.fine_to_coarse``.
Note the ``outline`` and ``keepout`` arguments being passed to the ``Layer`` constructors.

.. literalinclude:: experiment_generate_beginner3.py
   :language: python
   :linenos:
   :lines: 5-32

The rest of the code is almost the same as in :ref:`experiment_generate_beginner1`:

.. literalinclude:: experiment_generate_beginner3.py
   :language: python
   :linenos:
   :lines: 34-59

.. image:: experiment_generate_beginner3.png

.. image:: experiment_generate_beginner3_zoom.png


Reference
=========

.. literalinclude:: experiment_generate_beginner3.py
   :language: python
   :linenos:
   :lines: 1-59
