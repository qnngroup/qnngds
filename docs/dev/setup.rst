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
      cd qnngds

* Create a new virtual environment. Follow the instructions `here <https://qnngds.readthedocs.io/en/latest/tutorials/gettingstarted.html#setup-a-virtual-environment-and-install-qnngds>`_.

* From within the same directory, install ``qnngds`` as an editable package:

    * Using ``conda`` or ``python`` ``venv``:

        .. code-block:: bash

            pip install -e .

    * Using ``uv``

        .. code-block:: bash

            uv pip install -e .

2. Start coding
---------------

* Before you start coding, install `pre-commit <https://pre-commit.com/>`_ and run
  it in the repository root directory:

  .. code-block:: bash

    [uv] pip install pre-commit
    pre-commit install

  This will add lint/autoformatting checks that run before each commit, as well as
  checks to make sure you don't accidentally commit unresolved merge conflicts or
  commit directly to master.

* When you're ready to make changes to the source code, make sure you create a new
  branch of the git. To do so, open a terminal and execute:

  .. code-block:: bash

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
