.. _Getting-Started:

Getting started
===============

Setup a virtual environment and install ``qnngds``
--------------------------------------------------
1. Create a new git repository with ``git init``, or follow the instructions at `<https://github.com/qnngroup/qnn-repo-template>`_ to clone a template repository.
This is where your new project will go.

2. In the same directory as the new git repository, create a new virtual environment.

    * Using ``conda`` (recommended, `miniforge installation instructions <https://github.com/conda-forge/miniforge?tab=readme-ov-file#install>`_):

        * Execute:

          .. code-block:: bash

              conda create -n my-project-env python=3.12
              conda activate my-project-env

        * Install ``qnngds`` (see step 3 below)

    * Using ``uv`` (recommended, `installation instructions <https://docs.astral.sh/uv/#installation>`_):

        * Open a terminal in the directory you want to put your virtual environment.

        * Execute:

          .. code-block:: bash

              uv venv --python 3.12

        * Follow the instructions from ``uv`` to activate the environment, as they will differ depending on the platform.

        * Install ``qnngds`` (see step 3 below)

    * Using ``python`` virtual environment is dispreffered, since one may need to manually install separate version of python if the system python version does not match the requirements for ``qnngds``.

3. Install ``qnngds``.

    .. note::

       If you are on windows, you will need to install gdspy manually before installing qnngds. You will need to download the prebuilt wheel file at [github.com/hetizmann/gdspy/releases](https://github.com/heitzmann/gdspy/releases/tag/v1.6.12).
       If you've followed the instructions this far, you've installed ``python3.12``, but the wheel was built with ``python3.8``. To disable the version check, replace ``cp38`` with ``cp312`` (or the appropriate version string based on the installed python version) in the filename for the wheel.
       Then run the following:

       .. code-block:: bash

            pip install path/to/gdspy-1.6.12-cp312-cp312-win_amd64.whl

   Now that you've activated your venv, install the package from pypi.

    * Using ``conda`` or ``python`` ``venv``:

        .. code-block:: bash

            pip install qnngds

    * Using ``uv``

        .. code-block:: bash

            uv pip install qnngds

Installing unreleased development versions of ``qnngds``
--------------------------------------------------------

.. note::

    This process is not tested on Windows. It should work, but it's possible additional programs need to be installed.

1. To install a development version of ``qnngds`` that hasn't been released on pypi yet, first clone ``qnngds`` from github onto your local machine.
2. Follow steps 1 and 2 from the above section.
3. When installing ``qnngds``, replace the command ``[uv] pip install qnngds`` with ``[uv] pip install -e /path/to/cloned/copy/of/qnngds``.
   Note that this will be a different path from the repo you set up earlier.
