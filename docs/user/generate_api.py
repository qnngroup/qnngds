import os

def generate_api_rst(filename):
    content = "API\n===\n\n"

   # Define preferred order for plotting folders
    preferred_order = ['devices', 'circuits', 'geometries', 'utilities', 'design']

    # Iterate through preferred order
    for subfolder in preferred_order:
        content += f"{subfolder.capitalize()}\n"
        content += f"{'-' * len(subfolder)}\n\n"
        content += f".. automodule:: qnngds.{subfolder}\n"

        # Add images from the subfolder
        subfolder_path = os.path.join(os.path.dirname(__file__), 'images', subfolder)
        images = sorted([f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))])
        content += f"    :members:\n"
        content += f"    :exclude-members: {', '.join(os.path.splitext(i)[0] for i in images)}\n"
        content += f"    :undoc-members:\n"
        content += f"    :show-inheritance:\n\n"

        for image in images:
            figurename, ext = os.path.splitext(image)
            content += f"    .. autofunction:: {figurename}\n\n"
            content += f"        .. image:: images/{subfolder}/{image}\n"
            content += f"            :alt: {image}\n\n"

    with open(filename, 'w') as file:
        file.write(content)

if __name__ == "__main__":
    generate_api_rst("api.rst")
