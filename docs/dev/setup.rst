.. _Setup:

Setup
=====


Setup your workspace
--------------------
* Create a new folder that will contain everything related to your new design
  (versions, gds files, notes).

* Clone the repository:

  .. code-block:: bash

      git clone https://github.com/qnngroup/qnngds.git


* Create a new virtual environment:

    * Open a terminal in the directory you want to put your virtual environment.

    * Execute:

      .. code-block:: bash

          python -m venv/your-env-name
          .\.venv\your-env-name\Scripts\Activate


Install the package
-------------------
The qnngds package needs gdspy to be installed first. To do so, you can follow
instruction `here <https://pypi.org/project/gdspy/>`_. For windows, what works
best is to `install a pre-built wheel
<https://github.com/heitzmann/gdspy/releases>`_ and run :

.. code-block:: bash

    pip install path/to/gdspy-1.6.12-cp38-cp38-win_amd64.whl

Make sure you download the wheel corresponding to your device:

* `cpXX` is the version of python that it is built for.
* `winxx_amdXX` should be selected based on your system type.

Once gdspy is installed in your virtual environment, you can install qnngds
package (that you intend to modify) by executing:

.. code-block:: bash
    
    cd path/to/qnngds
    pip install .

.. note::
    If any, make sure to delete the `.pdm-build` folder before trying to run the 
    previous steps.

You should now be able to run every module of src/qnngds without errors.
You are ready to continue to :ref:`Coding` section.