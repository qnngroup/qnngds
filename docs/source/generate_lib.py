import os

def generate_libraries_rst(filename):
    content = """
Libraries
=========

"""

    # Iterate through subfolders in the images directory
    images_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
    subfolders = [f for f in os.listdir(images_dir) if os.path.isdir(os.path.join(images_dir, f))]

    for subfolder in subfolders:
        content += f"{subfolder}\n"
        content += f"{'=' * len(subfolder)}\n\n"

        # Add images from the subfolder
        subfolder_path = os.path.join(images_dir, subfolder)
        images = [f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]
        for image in images:
            content += f".. image:: ../images/{subfolder}/{image}\n"
            content += f"   :alt: {image}\n\n"

    with open(filename, 'w') as file:
        file.write(content)

if __name__ == "__main__":
    generate_libraries_rst("libraries.rst")
