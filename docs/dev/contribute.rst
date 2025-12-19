.. _doc for contributors:

Documentation for qnngds' contributors
======================================

You are a user of the package and wish to complete it with your newly created
functions. You will find here the instructions to contribute to the package.

There are two ways to contribute your new functions.
The preferred route for contribution is generally to open a pull request to merge your changes into ``qnngds``.
However, in some cases, the functionality introduced is very closely intertwined with specifics of the PDK in use (this is often the case for circuits comprised of many devices, although may not be for simple single-layer circuits), and as such does not make sense to include in ``qnngds``.
Or, it's possible that the design is confidential or otherwise not appropriate for public release.
In these cases, it is preferred to open a pull request to merge your changes into your private PDK template repo (e.g. ``qnngds-pdk``).

.. warning::
  Be careful, if you are contributing to ``src`` (e.g. creating a new device or cell),
  make sure your branch does **not** start with ``dev-``; this prefix is reserved for
  updates to the documentation or packaging, and CI/CD workflows will not run properly.

0. What and where to add
------------------------

Before contributing to the package, make sure its structure and organization are
clear to you. The contributions should go in the same direction as how the
package was thought in terms of hierarchy. If you are already a user of the
package, the contribution should be quite straighforward; otherwise, please
first refer to `qnngds user's documentation
<https://qnngds.readthedocs.io/en/latest/>`_, you can also check the `tutorials
<https://qnngds.readthedocs.io/en/latest/tutorials.html>`_.

.. _Comment your functions:

1. Document your functions
-------------------------

When adding a new function to the package, it is essential to properly document
it. This package is meant to be used by everyone; the function docstring should
include a brief (but clear) **description** of what it does, followed by a
deeper explaination if needed. Every **parameter** should have a type and
explanation attached, same for the **return**. You can add **examples** of how
to use the function if this helps making its use clearer.

Additionally, a given format of the function's docstring should be respected.
Indeed, the documentation is automatically generated and will not work properly
if the :ref:`format<docstring format>` is not respected.

.. _docstring format:

See `the Google Python Style Guide
<https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`_
for more details.

.. code-block:: python

    def your_function_name(param1: type, param2: type) -> type:
        """
        Brief description of the function.

        Args:
            param1 (type): Description of param1.
                This description might take several lines, in this case it needs
                an indentation.
            param2 (type): Description of param2.

        Returns:
            return_type: Description of the return value.

        Raises:
            SpecificException: Description of when this exception is raised.

        Examples:
            Example usage of the function.
        """
        # Implementation of the function

2. Registering devices
----------------------

If your newly-added functions are intended to be used to generate a ``Device``
instance, make sure to do the following:

1. Register them with the ``@qnngds.device`` `decorator <https://qnngds.readthedocs.io/en/latest/api.html#decorator>`_.
2. Provide default values for all arguments.

The first requirement ensures that the ``docs/user/generate_api.py`` documentation
generation script can generate images of the various ``Devices`` that are produced.
In addition, the second requirement ``generate_api.py`` ensures that a default image
can be generated.

3. Autodocs
-----------

.. note:
   Several scripts are included in the readthedocs CI/CD workflow that automate generation
   of documentation, including generation of images of Devices, as well as autogeneration
   of tutorials written as python files in docs/user/tutorials/. Normally, the automated CI/CD
   workflows are sufficient, however sometimes one may wish to run these manually on their
   local machine to check the outputs when debugging new functions or tutorials to avoid
   having to make a lot of commits.

If you need to manually generate the API, run

.. code-block:: bash

    python /path/to/qnngds/docs/user/generate_api.py

Executing this file will automatically call the ``plot_images.py`` script. This
script saves ``.png`` images for every function that returns a ``Device`` object.
Then, it generates the updated restructured text file for the API including your
contribution.  The generated API inlines the plotted images of the devices.

If you need to manually generate the reStructuredText or images for tutorials, run

.. code-block:: bash

    python /path/to/qnngds/docs/user/generate_tutorials.py

Executing this file will automatically generate the files necessary for tutorials.
See the python files in `docs/user/tutorials/` for examples of tutorial scripts.

.. _rtd version in qnngds:

3. Preview the documentation: automatic versioning
--------------------------------------------------

Before opening a pull request, verify the changes you made to the package are well
generated and properly display in the documentation. When pushing your code on
your branch, a new verison of qnngds' documentation will be accessible.

Commit your changes on a new branch:

.. code-block:: bash

    git add .
    git commit -m "Your descriptive commit message"

Push your branch to GitHub:

* If you are pushing a new branch for the first time:

  .. code-block:: bash

      git push [--set-upstream] origin your_new_branch_name

* Any other time, you can simply use:

  .. code-block:: bash

      git push

Open the `documentation <https://qnngds.readthedocs.io/en/latest/>`_. You will
find on the bottom left corner of the page something like ``v: latest``. Click
on it and select the version corresponding to your branch. Your changes should
appear in this documentation's version. Check that the API displays properly and
that your new devices are part of the libraries (if applicable).

.. note:: Cannot see your documentation's version?
    * Be patient and refresh the page

    * Check the `Read The Docs <https://readthedocs.org/projects/qnngds/>`_
      project to make sure your verison is processing


4. Satisfied with your code, ready for a pull request
-----------------------------------------------------

If you are satisfied with the modifications made to the package, and that the
document was correctly updated, you are ready for a pull request.

.. _version package:

In ``pyproject.toml``, manually update the ``version = x.x.x``. If your name is
not yet cited, add it to the ``authors``! Below is a table explaining how to
update the version. To avoid any mistake, you can check the latest version built
in the project's `history <https://pypi.org/project/qnngds/#history>`_.

+-------------------------+----------------------+--------------------------+------------------------+
| Code status             | Stage                | Rule                     | Example version        |
+=========================+======================+==========================+========================+
| First release           | New product          | Start with 1.0.0         | 1.0.0                  |
+-------------------------+----------------------+--------------------------+------------------------+
| | Backward compatible   | Patch release        | | Increment the third    | 1.0.1                  |
| | bug fixes             |                      | | digit                  |                        |
+-------------------------+----------------------+--------------------------+------------------------+
| | Backward compatible   | Minor release        | | Increment the middle   | 1.1.0                  |
| | new features          |                      | | digit and reset last   |                        |
|                         |                      | | digit to zero          |                        |
+-------------------------+----------------------+--------------------------+------------------------+
| | Changes that break    | Major release        | | Increment the first    | 2.0.0                  |
| | backward compatibility|                      | | digit and reset middle |                        |
|                         |                      | | and last digits to zero|                        |
+-------------------------+----------------------+--------------------------+------------------------+

You can now **create a pull request**. A new version of the ``qnngds`` package
will automatically be built (using the updated version number you indicated)
after the request is accepted.
