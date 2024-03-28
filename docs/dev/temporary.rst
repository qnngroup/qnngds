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

explain that the python package will be auto built when the pull request is accepted and pushed from main

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

You plan to touch to the dev folder? Add a ``dev`` prefix to your branch.
You will need to build test versions of the PyPI package? Use ``dev-pypi`` prefix.

Modification relative to the documentation
------------------------------------------

Modifying the documentations structure:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

two docs independent: dev and user 

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

More links
~~~~~~~~~~
* CICD for rtd
* RTD basics




Modification relative to the PyPI package
-----------------------------------------