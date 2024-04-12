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
instruction `here <https://pypi.org/project/gdspy/>`_.

For windows, what works
best is to `install a pre-built wheel
<https://github.com/heitzmann/gdspy/releases>`_ and run :

.. code-block:: bash

    pip install path/to/gdspy-1.6.12-cp38-cp38-win_amd64.whl

Make sure you download the wheel corresponding to your device:

* `cpXX` is the version of python that it is built for.
* `winxx_amdXX` should be selected based on your system type.

On Linux, just install with pip :

.. code-block:: bash

    pip install gdspy

Once gdspy is installed in your virtual environment, you can install **qnngds**
package (that you intend to modify) in editable mode. This allows to test the
changes made to the package without having to reinstall it every time.

.. code-block:: bash

    pip install -e /path/to/qnngds

.. note::
    If any, make sure to delete the ``.pdm-build`` folder before trying to run the 
    previous steps.

3. Start coding
---------------

Before you start coding, install `pre-commit <https://pre-commit.com/>`_ and run it in the repository root directory:

Install with pip

.. code-block:: bash

    pip install pre-commit


Add the precommit hooks to your local copy of ``qnngds``
.. code-block:: bash

    pre-commit install

This will add lint/autoformatting checks that run before each commit, as well as checks to make sure you don't accidentally commit unresolved merge conflicts or commit directly to master.

When you're ready to make changes to the source code, make sure you create a new branch of the git. To do so,
open a terminal and execute:

.. code-block:: bash

    cd path/to/qnngds
    git checkout -b your-branch-name

You can now modify the package as wanted. 

Continue to the :ref:`documentation for qnngds' contributors<doc for
contributors>` if you have functions to add to the package (most standard case). 

Continue to the :ref:`documentation for qnngds' developers<doc for developers>`
if you have deeper modifications to make to the package.
