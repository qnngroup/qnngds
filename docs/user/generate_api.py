import os
from images import plot_images


def automodule(module, image_folder):
    """Generates the documentation block for a specific module with links to
    images for each function.

    Args:
        module (str): The module file name (e.g., 'module.py').
        image_folder (str): The folder where images corresponding to the module's functions are stored.

    Returns:
        str: A string containing the Sphinx documentation directives for the module including
             links to function images.

    This function constructs a string that is formatted as an automodule directive for Sphinx.
    It includes images stored in a specified subdirectory that match the names of the functions
    in the module. The function assumes that images are named similarly to the functions they
    correspond to and are stored in a folder structure that mirrors the module structure under
    a base 'images' directory.
    """
    content = f".. automodule:: qnngds.{module[:-3]}\n"

    # Add images from the image folder
    image_folder_path = os.path.join(os.path.dirname(__file__), "images", image_folder)
    images = sorted(
        [
            f
            for f in os.listdir(image_folder_path)
            if os.path.isfile(os.path.join(image_folder_path, f))
            and not f.startswith("_")
        ]
    )
    content += "    :members:\n"
    content += (
        f"    :exclude-members: {', '.join(os.path.splitext(i)[0] for i in images)}\n"
    )
    content += "    :undoc-members:\n"
    content += "    :show-inheritance:\n\n"

    for image in images:
        figurename, ext = os.path.splitext(image)
        content += f"    .. autofunction:: {figurename}\n\n"
        content += f"        .. image:: images/{image_folder}/{image}\n"
        content += f"            :alt: {image}\n\n"

    return content


def generate_api(src_path):
    """Generates the complete API documentation for all modules in a given
    source directory.

    Args:
        src_path (str): The path to the source directory containing the Python modules.

    This function constructs a complete API documentation file in reStructuredText format by iterating
    over all Python modules in the specified source path. For each module, it calls `automodule` to get
    the documentation block and compiles these into a single documentation file.
    """

    api = "API\n===\n\n"

    modules = [m for m in os.listdir(src_path) if not m.startswith("_")]
    for module in sorted(modules):
        if module.endswith(".py"):
            api += f".. _{module[:-3].capitalize()}:\n"  # For referencing this section
            api += f"{module[:-3].capitalize()}\n"  # The section title
            api += f"{'-' * len(module[:-3])}\n\n"  # -----------------
            api += automodule(module, image_folder=module[:-3])
        else:
            api += f".. _{module.capitalize()}:\n"  # For referencing this section
            api += f"{module.capitalize()}\n"  # The section title
            api += f"{'-' * len(module)}\n\n"  # -----------------
            api += f".. automodule:: qnngds.{module}\n\n"
            module_path = os.path.join(src_path, module)

            submodules = sorted(
                [
                    m
                    for m in os.listdir(module_path)
                    if not m.startswith("_") and m.endswith(".py")
                ]
            )

            for submodule in submodules:
                api += f"{submodule[:-3]}\n"  # The subsection title
                api += f"{'~' * len(submodule[:-3])}\n\n"  # ~~~~~~~~~~~~~~~~~~~~
                api += automodule(
                    f"{module}.{submodule}", image_folder=f"{module}/{submodule[:-3]}"
                )

    with open("api.rst", "w") as file:
        file.write(api)


if __name__ == "__main__":
    qnngds_path = os.path.join("..", "..", "src", "qnngds")

    try:
        plot_images.process_modules_in_folder(qnngds_path)
        generate_api(qnngds_path)

    except FileNotFoundError as e:
        print(e)
        print(
            "\nMake sure you are executing the file in the correct directory. "
            "To fix this, you can run: \n"
        )
        current_file_path = os.path.realpath(__file__)
        parent_folder = os.path.dirname(current_file_path)
        print("     cd ", parent_folder)
        print()
