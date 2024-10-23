.. _Setup:

Setup
=====

1. Setup your workspace
-----------------------

In order to contribute to ``qnngds``, you will need to clone the repository.
It is **strongly** recommended to set up a virtual environment or conda environment so that you can continue to use a stable version of ``qnngds`` for designing layouts.

* Open a terminal where you want the ``qnngds`` folder to be. Clone the
  repository:

  .. code-block:: bash

      git clone git@github.com/qnngroup/qnngds.git

* Create a new virtual environment:

    * Open a terminal in the directory you want to put your virtual environment.

    * Create a ``venv`` with python (by default uses the system python version):

      .. code-block:: bash

          python -m venv/your-env-name
          .\.venv\your-env-name\Scripts\Activate

    * Alternatively, create a conda environment (useful if you want to include other non-python packages):

      .. code-block:: bash

          conda create -n qnngds-dev python=3.x
          conda activate qnngds-dev


2. Install the package
----------------------

* On **windows** systems, the qnngds package needs ``gdspy`` to be installed first. To do so, you can follow instruction `here <https://pypi.org/project/gdspy/>`_.
  First, `install a pre-built wheel <https://github.com/heitzmann/gdspy/releases>`_ 
  and run :

  .. code-block:: bash

    pip install path/to/gdspy-1.6.12-cp38-cp38-win_amd64.whl

  Make sure you download the wheel corresponding to your device:

    * `cpXX` is the version of python that it is built for.
    * `winxx_amdXX` should be selected based on your system type.

* On **Linux**, ``gdspy`` can be installed with ``pip``, so no action is needed.

Once ``gdspy`` is installed in your virtual environment, you can install ``qnngds``
package (that you intend to modify) in editable mode. This allows to test the
changes made to the package without having to reinstall it every time.
Be sure to specify the same path as you downloaded the repository to in Step 1.

.. code-block:: bash

    pip install -e /path/to/qnngds

.. note::
    If any issues come up, delete the ``.pdm-build`` folder before trying to run the 
    previous steps.

3. Start coding
---------------

* Before you start coding, install `pre-commit <https://pre-commit.com/>`_ and run 
  it in the repository root directory:

  .. code-block:: bash

    pip install pre-commit
    pre-commit install

  This will add lint/autoformatting checks that run before each commit, as well as 
  checks to make sure you don't accidentally commit unresolved merge conflicts or 
  commit directly to master.

* When you're ready to make changes to the source code, make sure you create a new 
  branch of the git. To do so, open a terminal and execute:

  .. code-block:: bash

    cd path/to/qnngds
    git checkout -b your-branch-name

.. warning::
  Be careful, if you are contributing to ``src`` (e.g. creating a new device or cell),
  make sure your branch does **not** start with ``dev-``; this prefix is reserved for
  updates to the documentation or packaging.

You can now modify the package as wanted. 

Continue to the :ref:`documentation for qnngds' contributors<doc for
contributors>` if you have functions to add to the package (most standard case). 

Continue to the :ref:`documentation for qnngds' developers<doc for developers>`
if you have deeper modifications to make to the package.
