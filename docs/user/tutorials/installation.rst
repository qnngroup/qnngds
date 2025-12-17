Getting started
===============

Setup a virtual environment and install ``qnngds``
--------------------------------------------------
1. Create a new git repository with `git init`, or follow the instructions at `<https://github.com/qnngroup/qnn-repo-template>`_ to clone a template repository.

2. In the same directory as the new git repository, create a new virtual environment:

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

    * Using ``python`` virtual environment (dispreffered, since one has to manually install separate version of python):

        * Open a terminal in the directory you want to put your virtual environment.

        * Execute:

          .. code-block:: powershell

              # windows
              python -m venv .venv/your-env-name
              .\.venv\your-env-name\Scripts\Activate

          .. code-block:: bash

              # Unix/macOS
              python -m venv .venv/your-env-name
              source .venv/your-env-name/scripts/activate

        * Install ``qnngds`` (see step 3 below)

3. Install ``qnngds``.

   Now that you've activated your venv, install the package from pypi.

    * Using ``conda`` or ``python`` ``venv``:

        .. code-block:: bash

            pip install qnngds

    * Using ``uv``

        .. code-block:: bash

            uv pip install qnngds


Installing unreleased development versions of ``qnngds``
--------------------------------------------------------
1. To install a development version of ``qnngds`` that hasn't been released on pypi yet, first clone ``qnngds`` from github onto your local machine.
2. Follow steps 1 and 2 from the above section.
3. When installing ``qnngds``, replace the command ``[uv] pip install qnngds`` with ``[uv] pip install -e /path/to/cloned/copy/of/qnngds``.
   Note that this will be a different path from the repo you set up earlier.
