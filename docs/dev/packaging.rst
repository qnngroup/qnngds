.. _Packaging:

Packaging 
=========

*<https://packaging.python.org/en/latest/tutorials/packaging-projects/>
Explain the docs present in this package (pyproject.toml, license, readme etc)

Explain how to update the pypi package (discuss who should have access to this :
should everyone be able to push to the main and update the package etc or shoul
dit be peered reviewed first ?)
once the pull request is accepted, the assignees should follow the next steps to update the package on python:

Figure out the token/account issue. *


#. Modify the code as needed, see :ref:`Coding` for instructions and guides.

    .. note::
        When testing the code, you can install the package in development mode. This allows to test the changes made 
        to the package without having to reinstall it every time. To do so, open a terminal in the **qnngds** directory and execute:

        .. code-block:: bash

            cd path/to/qnngds
            pip install -e /path/to/qnngds

#. In **``pyproject.toml``**, manually update the ``version``.

#. Delete **``.pdm-build``** and **``dist``** folders.

#. Open terminal in **qnngds** directory. Run the following commands:
    
    .. code-block:: bash

        py -m build
        twine upload dist/*
    
    Enter the token password. (Note that Ctrl+V might not work, you need to use Right Click `>` Edit '>' Paste)

    .. warning::
        Before executing the commands above, make sure you have the latest version of PyPA's **build** and **twine**:

        .. code-block:: bash

            py -m pip install --upgrade build
            py -m pip install --upgrade twine



