Coding
=======

GitHub Management
-----------------

To contribute to our package, follow these steps:

1. Clone the repository:
git clone https://github.com/qnngroup/qnngds.git

2. Create a new branch for your work:
git checkout -b your_new_branch_name

3. Start adding your functions or making changes to existing ones.

4. Once you're done, commit your changes:
git add .
git commit -m "Your descriptive commit message"

5. Push your branch to GitHub:
git push origin your_new_branch_name

6. Finally, create a pull request on GitHub to merge your changes into the main branch.


Package Structure
-----------------

The package is organized as follows:

- the source code, i.e. the package modules
    - devices: 
    - circuits:
    - geometries: 
    - utilities: 
    - design: 
- some files for creating the package
- some files for documenting it

See more details on how to contribute to the package and documentation files in
sections :ref:`Packaging` and :ref:`Documenting`.

Good Coding Practices
---------------------

When contributing code to the package, please follow these practices:

- Avoid lines of code that are too long; break them for readability.
- Comment your functions and code for better understanding.
- Include type annotations for function parameters and return types.

Function Docstring Template (Google Format)
-------------------------------------------

```python
def your_function_name(param1: type, param2: type) -> return_type:
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
 ```