.. _Setup:

Setup
=====

1. Setup your workspace
-----------------------

* Open a terminal where you want the ``qnngds`` folder to be. Clone the
  repository:

  .. code-block:: bash
      git clone https://github.com/qnngroup/qnngds.git

* Create a new virtual environment:

    * Open a terminal in the directory you want to put your virtual environment.

    * Execute:

      .. code-block:: bash
          python -m venv/your-env-name
          .\.venv\your-env-name\Scripts\Activate


2. Install the package
----------------------

The qnngds package needs **gdspy** to be installed first. To do so, you can follow
instruction `here <https://pypi.org/project/gdspy/>`_. For windows, what works
best is to `install a pre-built wheel
<https://github.com/heitzmann/gdspy/releases>`_ and run :

.. code-block:: bash
    pip install path/to/gdspy-1.6.12-cp38-cp38-win_amd64.whl

Make sure you download the wheel corresponding to your device:

* `cpXX` is the version of python that it is built for.
* `winxx_amdXX` should be selected based on your system type.

Once gdspy is installed in your virtual environment, you can install **qnngds**
package (that you intend to modify) in editable mode. This allows to test the
changes made to the package without having to reinstall it every time.

.. code-block:: bash
    pip install -e /path/to/qnngds

.. note::
    If any, make sure to delete the `.pdm-build` folder before trying to run the 
    previous steps.

3. Start coding
---------------

Before you start coding, make sure you create a new branch of the git. To do so,
open a terminal and execute:

.. code-block:: bash
    cd path/to/qnngds
    git checkout -b your-branch-name

You can now modify the package as wanted. 

Continue to the :ref:`documentation for qnngds' contributors<doc for
contributors>` if you have functions to add to the package (most standard case). 

Continue to the :ref:`documentation for qnngds' developers<doc for developers>`
if you have deeper modifications to make to the package.

.. _doc for contributors:

Documentation for qnngds' contributors
======================================

You are a user of the package and wish to complete it with your newly created
functions. You will find here the instructions to contribute to the package.

Be careful, make sure the branch you are working on does **not** start with
``dev-``, this prefix is reserved for developers.
 
0. What and where to add
------------------------

* New **test structures** (alignment marks, vdp...) and new **geometries**
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

.. _Comment your functions:

1. Comment your functions
-------------------------

When adding a new function to the package, it is essential to properly document
it. This package is meant to be used by everyone, the function docstring should
include a brief (but clear) **description** of what it does, followed by a
deeper explaination if needed. Every **parameter** should have a type and
explanation attached, same for the **return**. You can add **examples** of how
to use the function if this helps making its use clearer.

Additionally, a given format of the function's docstring should be respected.
Indeed, the documentation is automatically generated and will not work properly
if the :ref:`format<docstring format>` is not respected.

.. todo::
    Add pre-commit hooks with auto-formatting (black, ruff).

.. _docstring format:

See `the Google Python Style Guide
<https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_
for more details.

.. code-block:: python

    def your_function_name(param1: type, param2: type) -> type:
        """
        Brief description of the function.

        Args:
            param1 (type): Description of param1.
                This description might take several lines, in this case it needs
                an indentation.
            param2 (type): Description of param2.

        Returns:
            return_type: Description of the return value.

        Raises:
            SpecificException: Description of when this exception is raised.

        Examples:
            Example usage of the function.
        """
        # Implementation of the function

2. Build the libraries
----------------------

.. todo::
    Check how to automate that, running generate images and generate libraries 
    before pull request?

If the function created returns a Device object, it should be added to the
library. You could manually upload the quickplot of this function by saving it
to ``docs>user>images>module-containing-your-function`` under
``your-function.png`` name. However, you can also follow these steps to
auto-generate the qnngds library:

#. Open a terminal in ``/path-to-qnngds/docs/user/images`` and run
   ``plot_images.py`` file. This will automatically create png images of
   returned devices of every function in the qnngds package.

#. Open a terminal in ``/path-to-qnngds/docs/user`` and run
   ``generate_libraries.py`` file. This will automatically generate the
   ``libraries.rst`` file.

.. _rtd version in qnngds:

3. Preview the documentation: automatic versioning
--------------------------------------------------

You might want to check that the changes you made to the package are well
generated in the documentation. When pushing your code on your branch, a new
verison of qnngds' documentation will be accessible.

Commit your changes:

.. code-block:: bash
    git add .
    git commit -m "Your descriptive commit message"

Push your branch to GitHub:

* If you are pushing a new branch for the first time:

  .. code-block:: bash
      git push origin your_new_branch_name 

* Any other time, you can simply use:

  .. code-block:: bash
      git push

Open the `documentation <https://qnngds.readthedocs.io/en/latest/>`_. You will
find on the bottom left corner of the page something like ``v: latest``. Click
on it and select the version corresponding to your branch. Your changes should
appear in this documentation's version. Check that the API displays properly and
that your new devices are part of the libraries (if applicable).

.. note:: Cannot see your documentation's version? 
    * Be patient and refresh the page

    * Check the `Read The Docs <https://readthedocs.org/projects/qnngds/>`_
      project to make sure your verison is processing


4. Satisfied with your code, ready for a pull request
-----------------------------------------------------

If you are satisfied with the modifications made to the package, and that the
document was correctly updated, you are ready for a pull request.

.. _version package:

In ``pyproject.toml``, manually update the ``version = x.x.x``. If your name is
not yet cited, add it to the ``authors``! Below is a table explaining how to
update the version. To avoid any mistake, you can check the latest version built
in the project's `history <https://pypi.org/project/qnngds/#history>`_.

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

You can now **create a pull request**. A new version of the ``qnngds`` package
will automatically be built (using the updated version number you indicated)
after the request is accepted.

.. _doc for developers:

Documentation for qnngds' developers
====================================

You have deeper modifications to bring to the package, you will find here
informations relative to the package development.

The :ref:`Setup` is exactly the same than for contributors,
except for **one** difference: the name of your branch. Indeed, developers will
have access to platforms that normal contributors don't need. The CICD will not
work on your branch if they don't have the correct prefix. 

* You plan to touch to the ``dev`` folder? Add a ``dev-`` prefix to your branch.

* You need to build test versions of the PyPI package? Use ``dev-pypi`` prefix.

Modifications relative to the documentation
-------------------------------------------

The **qnngds documentation** is built as follow. The ``docs`` folder contains
two subfolders ``user`` and ``dev``. Those are two different Read the Docs
projects. This configuration allows to have two seperate documentations: one for
the package's users (`qnngds <https://qnngds.readthedocs.io/en/latest/>`_) and one
for the package's developers/contributors like you (`qnngds-dev
<https://qnngds.readthedocs.io/projects/qnngds-dev/en/latest/>`_). Both projects
share the same configuration file. 

.. seealso::
    For more details on multiprojects, see `Documentation for 
    sphinx-multiproject <https://sphinx-multiproject.readthedocs.io/en/latest/>`_.

As a **contributor**, you can already preview every modification you bring to the
qnngds documentation (for users), as described :ref:`above<rtd version in
qnngds>`. Every new branch will generate a new version of the documentation
(except a branch that starts with "dev").

.. warning::
    Some files useful for automating the documentation are not fully modular. For
    example, if the qnngds modules were to change names or some were to be
    added/deleted, you would also need to manually update them in
    ``generate_libraries.py`` and ``api.rst``. Modifying the package structure
    should be taken with great care.

As a **developer**, if you have precisions/modifications to bring to the
qnngds-dev documentation (for contributors and developpers), you will need to
create a branch which name starts with ``dev``. 

Every new dev-branch will generate a new version of the developer's
documentation, automatically updated when a push is send on this branch.

When you are satisfied with the new versions you created, you can go on and
create a pull request for review.

Modifications relative to the PyPI package
------------------------------------------

As a **contributor** to the package, you do not need to modify any of the webpages
of PyPI but only want to build a new version of it to be sure your modifications
have been included. 

However, as a **developer**, you may want to update things like the ``README``
file, the ``LICENSE``, or add more complex features to the package. In each
case, you will want to test those modifications before reveiling them to the
great world. 

When working on your new package, every push on your ``dev-pypi-yourbranch``
branch will automatically generate a build of a `test PyPI version of qnngds
package <https://test.pypi.org/project/qnngds/>`_. 

Like for the (real) PyPI package, and as explained :ref:`before<version
package>`, make sure you updated the test package ``version`` in the
``pyproject.toml`` file. To avoid any mistake, you can check the versions
already built in the project's `history
<https://test.pypi.org/project/qnngds/#history>`_.

.. warning::
    If you try to publish distribution to (test) PyPI with a version that
    already exist, the operation will fail and an email will be sent to the 
    owners of the project. See `GitHub's Actions 
    <https://github.com/qnngroup/qnngds/actions>`_ to follow builds. 

When you are satisfied with the new versions you created, you can go on and
create a pull request for review.
