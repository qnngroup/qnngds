import os


def automodule(module, image_folder):
    content = f".. automodule:: qnngds.{module[:-3]}\n"

    # Add images from the image folder
    image_folder_path = os.path.join(os.path.dirname(__file__), "images", image_folder)
    images = sorted(
        [
            f
            for f in os.listdir(image_folder_path)
            if os.path.isfile(os.path.join(image_folder_path, f))
        ]
    )
    content += f"    :members:\n"
    content += f"    :exclude-members: {', '.join(os.path.splitext(i)[0] for i in images)}\n"
    content += f"    :undoc-members:\n"
    content += f"    :show-inheritance:\n\n"

    for image in images:
        figurename, ext = os.path.splitext(image)
        content += f"    .. autofunction:: {figurename}\n\n"
        content += f"        .. image:: images/{image_folder}/{image}\n"
        content += f"            :alt: {image}\n\n"

    return content


def generate_api(src_path):
    api = "API\n===\n\n"

    modules = [m for m in os.listdir(src_path) if not m.startswith('__')]
    for module in modules:
        if module.endswith('.py'):
            api += f"{module[:-3].capitalize()}\n"
            api += f"{'-' * len(module[:-3])}\n\n" 
            api += automodule(module, image_folder=module[:-3])
        else:
            api += f"{module.capitalize()}\n"
            api += f"{'-' * len(module)}\n\n"
            module_path = os.path.join(src_path, module)
            submodules = [m for m in os.listdir(module_path) if not m.startswith('__') and m.endswith('.py')]
            for submodule in submodules:
                api += f"{submodule[:-3]}\n"
                api += f"{'~' * len(submodule[:-3])}\n\n" 
                api += automodule(f"{module}.{submodule}", image_folder=f"{module}/{submodule[:-3]}")

    with open("api.rst", "w") as file:
        file.write(api)

if __name__ == "__main__":
    qnngds_path = os.path.join("..", "..", "src", "qnngds")
    generate_api(qnngds_path)