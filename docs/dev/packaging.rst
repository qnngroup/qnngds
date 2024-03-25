.. _Packaging:

Packaging 
=========

This section has to be executed by someone who is an owner or a maintainer of
the `qnngds PyPI project <https://pypi.org/project/qnngds/>`_. Only the owners of the project can add
contributors. 

.. note:: 
  In **QNN group**, the maintainers and owners are also the ones who
  validate the pull request you make to the GitHub. It is their role to update the
  package after a pull request has been accepted.

First Time Maintainer Guideline
-------------------------------

If you wish to be a maintainer of the **qnngds PyPI project**, you will have to follow these steps:

* Create a `PyPI account <https://pypi.org/account/register/>`_

* Verify your e-mail address in PyPI.

* Create an `API token <https://pypi.org/help/#apitoken>`_. 

  * name = ``__token__``

  * password: make sure you copy your token password before closing the window,
    you will not be able to access it later for security reasons.

* Contact one of the owner to ask them to add you to the project, provide them your PyPI username.


.. _Updating qnngds package:

Updating qnngds package after a pull request has been accepted
--------------------------------------------------------------

#. Modify the code as needed, see :ref:`Coding` for instructions and guides.

   .. note::
       When testing the code, you can install the package in development mode. 
       This allows to test the changes made to the package without having to 
       reinstall it every time. To do so, open a terminal in the **qnngds** 
       directory and execute:

       .. code-block:: bash

           pip install -e /path/to/qnngds

#. In ``pyproject.toml``, manually update the ``version = x.x.x``. If your name 
   is not yet cited, add it to the ``authors``!

#. Delete ``.pdm-build`` and ``dist`` folders.

#. Open terminal in **qnngds** directory. Run the following commands:
   .. warning::
       Before executing the commands below, make sure you have the latest version 
       of PyPA's **build** and **twine**:

       .. code-block:: bash

           py -m pip install --upgrade build
           py -m pip install --upgrade twine

   .. code-block:: bash

       py -m build
       twine upload dist/*

   Enter your token's password. (Note that Ctrl+V might not work, you need to use 
   Right-Click>Edit>Paste)

Modifying qnngds PyPI webpages
------------------------------

If you are looking to update/modify the PyPI webpage of qnngds, you will have to
modify files like ``README.md``, ``LICENSE.md`` or ``pyproject.toml``. Below are some
useful links that can help for this purpose. 

* `Python Packaging User Guide <https://packaging.python.org/en/latest/tutorials/
  packaging-projects/>`_  (for an introduction to packaging)

* `Writing your pyproject.toml <https://packaging.python.org/en/latest/guides/writing-
  pyproject-toml/>`_

* `Using TestPyPI <https://packaging.python.org/en/latest/guides/using-testpypi/>`_ to 
  try out the distribution tools and process without worrying about affecting the real index.

.. note::
    Once modified, a pull request has to be made as well and the :ref:`steps described 
    above<Updating qnngds package>` have to be followed.

.. todo::
    Figure out the visualization issue for modifying PyPI pages.



