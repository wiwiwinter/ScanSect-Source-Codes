import os
import shutil

# Change these paths
camera_import_folder = r"D:\TEST"        # where your camera dumps files
lightroom_input_folder = r"D:\IMAGES" # where Lightroom watches for imports

def move_images():
    for file in os.listdir(camera_import_folder):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.cr2', '.arw', '.nef')):
            src = os.path.join(camera_import_folder, file)
            dst = os.path.join(lightroom_input_folder, file)
            shutil.move(src, dst)
            print(f"Moved: {file}")

if __name__ == "__main__":
    move_images()