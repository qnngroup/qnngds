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
documentation, automatically updated when a push is sent on this branch.

When you are satisfied with the new versions you created, you can go on and
create a pull request for review.

.. seealso:: Useful links to create a documentation

    * `Read the Docs Documentation <https://docs.readthedocs.io/en/stable/>`_
    * `Sphinx Documentation <https://www.sphinx-doc.org/en/master/>`_

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

.. seealso:: Useful links to create a package

    * `Python Packaging User Guide
      <https://packaging.python.org/en/latest/tutorials/ packaging-projects/>`_

    * `Writing your pyproject.toml
      <https://packaging.python.org/en/latest/guides/writing- pyproject-toml/>`_

    * `Using TestPyPI
      <https://packaging.python.org/en/latest/guides/using-testpypi/>`_
