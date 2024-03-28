Documentation for contributors to qnngds
========================================

You are a user of the package and wish to complete it with your newly created
functions. 

Setup the project
-----------------

Be careful, make sure your branch does not start with "dev-", this prefix is reserved for developers.

include setup.rst

What and where to add
---------------------

* New **test structures** (alignement marks, vdp...) and new **geometries**
  (hyper taper...) go to ``geometries``.
* New **devices** (ntron, htron, snspd...) go to ``devices``.
* New **circuits** (logic gates, counter, any kinf of circuit made of
  devices...) go to ``circuits``.
* New **design tools** (functions useful for building designs) go to
  ``utilities``.
* New **cells** (made of circuits integrated with utilities tools) go to
  ``design``. 

.. todo::
    Reorganize design.

.. todo::
    Once design is reorganized, send the contributors to the tuto ``creating 
    your cell``. This is what every contributor should ideally go through when
    adding a new circuit to the package. 

Comment your functions
----------------------
include coding.rst comments docstring

.. _rtd version in qnngds:

explain how to visualize your branch version of documentation (to make sure it
is properly interpreted), explain how to run generate images and libraries.
These functions will always be usefull for this type of use.

.. todo::
    really figure out how to automate the libraries

Keep the code clean
-------------------
include coding.rst comments good coding practices

Satisfied with your code, ready for a pull request
--------------------------------------------------
Keep as little and specific as possible the content in each new branch. 

complete with end of coding github blabla

add the documenting few steps to manually build so far (create images, generate libraries)

.. todo:: 
    Automate the libraries build

explain that the user documentation will auto build when push from main.

explain that the python package will be auto built when the pull request is
accepted and pushed from main.
Explain that the contributor needs to MANUALLY update the version. Explain semantic versioning:
 
.. .. list-table:: Semantic Versioning
..     :widths: 30 20 35 15
..     :header-rows: 1

..     * - Code status
..       - Stage
..       - Rule
..       - Example version
..     * - First release
..       - New product
..       - Start with 1.0.0
..       - 1.0.0
..     * - Backward compatible |
..         bug fixes
..       - Patch release
..       - Increment the third digit
..       - 1.0.1
..     * - Backward compatible |
..         new features
..       - Minor release
..       - Increment the middle digit |
..         and reset last digit to zero
..       - 1.1.0
..     * - Changes that break backward |
..         compatibility
..       - Major release
..       - Increment the first digit |
..         and reset middle and last |
..         digits to zero
..       - 2.0.0

+-------------------------+----------------------+--------------------------+------------------------+
| Code status             | Stage                | Rule                     | Example version        |
+=========================+======================+==========================+========================+
| First release           | New product          | Start with 1.0.0         | 1.0.0                  |
+-------------------------+----------------------+--------------------------+------------------------+
| | Backward compatible   | Patch release        | | Increment the third    | 1.0.1                  |
| | bug fixes             |                      | | digit                  |                        |
+-------------------------+----------------------+--------------------------+------------------------+
| | Backward compatible   | Minor release        | | Increment the middle   | 1.1.0                  |
| | new features          |                      | | digit and reset last   |                        |
|                         |                      | | digit to zero          |                        |
+-------------------------+----------------------+--------------------------+------------------------+
| | Changes that break    | Major release        | | Increment the first    | 2.0.0                  |
| | backward compatibility|                      | | digit and reset middle |                        |
|                         |                      | | and last digits to zero|                        |
+-------------------------+----------------------+--------------------------+------------------------+


The END. (for contributors)

Still thirsty? 

Documentation for developers of qnngds
======================================

Setup 
-----

The setup is exactly the same than for contributors, except for **one**
difference: the name of your branch. Indeed, developers will have access to
platforms that normal contributors don't need. The CICD will not work on your
branch if they don't have the correct prefix. 

* You plan to touch to the ``dev`` folder? Add a ``dev-`` prefix to your branch.

* You need to build test versions of the PyPI package? Use ``dev-pypi`` prefix.

Modifications relative to the documentation
-------------------------------------------

The **qnngds documentation** is built as follow. The ``docs`` folder contains
two subfolders ``user`` and ``dev``. Those are two different Read the Docs
projects. This configuration allows to have two seperate documentations: one for
the package users (`qnngds <https://qnngds.readthedocs.io/en/latest/>`_) and one
for the developers/contributors like you (`qnngds-dev
<https://qnngds.readthedocs.io/projects/qnngds-dev/en/latest/>`_). Both projects
share the same configuration file. 

.. seealso::
    For more details on multiprojects, see `Documentation for 
    sphinx-multiproject <https://sphinx-multiproject.readthedocs.io/en/latest/>`_.

As a contributor, you can already preview every modification you bring to the
**qnngds documentation** (for users), as described :ref:`above<rtd version in
qnngds>`. Every new branch will generate a new version of the documentation
(except a branch that starts with "dev").

As a developer, if you have precisions/modifications to bring to the
**qnngds-dev documentation** (for contributors and developpers), you will need
to create a branch which name starts with "dev". Every new dev-branch will
generate a new version of the developer's documentation.

When you are satisfied with the new versions you created, you can go on and
create a pull request for review.

Modifications relative to the PyPI package
------------------------------------------

As a contributor to the package, you do not need to modify any of the webpages
of PyPI but only want to build a new version of it to be sure your modifications
have been included. 

As a developer, you may want to update things like the ``README`` file, the
``LICENSE``, or add more complex features to the package. In each case, you will
want to test those modifications before reveiling them to the great world. For
this purpose, a `test PyPI version of qnngds package
<https://test.pypi.org/project/qnngds/>`_ is automatically built every time code
is pushed from a branch having a ``dev-pypi`` prefix.
