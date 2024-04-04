import os

def generate_libraries_rst(filename):
    content = """
Libraries
=========

"""

   # Define preferred order for plotting folders
    preferred_order = ['devices', 'circuits', 'geometries', 'utilities', 'design']

    # Iterate through preferred order
    for subfolder in preferred_order:
        content += f"{subfolder}\n"
        content += f"{'-' * len(subfolder)}\n\n"

        # Add images from the subfolder
        subfolder_path = os.path.join(os.path.dirname(__file__), 'images', subfolder)
        images = [f for f in os.listdir(subfolder_path) if os.path.isfile(os.path.join(subfolder_path, f))]
        for image in images:
            figurename, ext = os.path.splitext(image)
            content += f"{figurename}\n"
            content += f"{'~' * len(figurename)}\n\n"

            content += f".. image:: images/{subfolder}/{image}\n"
            content += f"   :alt: {image}\n\n"

    with open(filename, 'w') as file:
        file.write(content)

if __name__ == "__main__":
    generate_libraries_rst("libraries.rst")
