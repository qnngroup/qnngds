.. _doc for developers:

Documentation for qnngds' developers
====================================

You have deeper modifications to bring to the package, you will find here
informations relative to the package development.

The :ref:`Setup` is exactly the same than for contributors.

Modifications relative to the documentation
-------------------------------------------

The **qnngds documentation** is built as follow. The ``docs`` folder
contains source files for generating the documentation.

Additional tutorials can be added under ``docs/src/tutorials/``.
A basic parser for literate programming can be found in ``docs/src/generate_tutorials.py``,
which allows you to write specially-commented code that will be rendered nicely.
See the `tutorials page <https://qnngds.readthedocs.io/en/latest/tutorials.html>`_ for some
examples.

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
case, you will want to test those modifications before revealing them to the
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
