
Documenting
===========

I am trying autosectionlabel extension :ref:`Documenting`.

Updating qnngds documentation after a code moficiation
------------------------------------------------------
.. _doc steps:
#. Modify the code as needed, see :ref:`Coding` for instructions and guides.

   Here, allow me to link again the :ref:`function docstring template<docstring
   template>` and emphasis on its importance. Indeed, if this format is not
   followed properly, the documentation will not correctly be displayed. 

   **If you want the documentation to be automated and simple, correctly document 
   the functions you create!**


.. warning::
    Some files useful for automating the documentation are not fully modular. For example, 
    if the qnngds modules were to change names or some were to be added/deleted, you would also need 
    to manually update them in ``generate_libraries.py`` and ``api.rst``. Modifying the package 
    structure should be taken with great care.

#. The functions you added should be part of the library?

   .. todo::
        Check how to automate that, running generate images and generate libraries 
        before pull request?

   If the function created returns a Device object, it should be added to the library.
   You could manually upload the quickplot of this function by saving it to
   ``docs>user>images>module-containing-your-function`` under
   ``your-function.png`` name. However, you can also follow these steps to
   auto-generate the qnngds library:

   #. Open a terminal in /path-to-qnngds/docs/user/images and run
      ``plot_images.py`` file. This will automatically create png images of
      returned devices of every function in the qnngds package.

   #. Open a terminal in /path-to-qnngds/docs/user and run
      ``generate_libraries.py`` file. This will automatically generate the
      ``libraries.rst`` file.

The next steps describe how to proceed if you are ready to make a pull request
but want to preview the documentation first. Jump to :ref:`this<latest rtd>`
step if you don't need to version the documentation.

#. Make sure you ``added``, ``committed`` and ``pushed`` your code to the branch 
   created for the modifications you brought.

#. In `Read The Docs <https://readthedocs.org/projects>`_, select **qnngds** project.

   .. todo::
       Figure out the shared rtd projects: ideally, every group member of qnngds should 
       be able to access it. To check.

#. Go to **Versions** and click on your branch. Select ``Activate`` and ``Hide`` for 
   this version to remain private.

#. Go to **Overview** and **build a version** after selecting your branch in the 
   dropdown list.

#. Your documentation's version is available in **View docs**!

   .. todo::
       Note that if you are note a manager of qnngds github, the CICD won't work on 
       your branch. Figure out who has access etc.

.. _latest rtd:
#. Once you are satisfied with how your documentation looks, you can generate
   the pull request. The documentation will automatically be built in the
   ``latest`` version. You will not need to manually generate the documentation
   in read the docs.


Modifying qnngds documentation's files
--------------------------------------

If you are looking to update/modify the qnngds documentation structure and
content, you will have to modify files like ``.readthedocs.yaml``, ``Makefile``,
``conf.py``, or any other ``file.rst``. Below are some useful links that can
help for this purpose. 

* `Read the Docs Documentation <https://docs.readthedocs.io/en/stable/>`_

* `Sphinx Documentation <https://www.sphinx-doc.org/en/master/>`_

The qnngds documentation is built as follow. The **docs** folder contains two
subfolders **user** and **dev**. Those are two different Read the Docs projects.
This configuration allows to have two seperate documentations: one for the
package users and one for the developers (you). They share the same
configuration file. For more details on multiprojects, see `sphinx-multiproject
Documentation <https://sphinx-multiproject.readthedocs.io/en/latest/>`_

.. note::
    If you are modifying this documentation (for qnngds developers), you can 
    follow the exact same :ref:`steps described above<doc steps>` to build your 
    documentation. The only difference is to open  **qnngds-dev** project instead 
    in `Read The Docs <https://readthedocs.org/projects>`_.


