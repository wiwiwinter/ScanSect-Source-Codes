import serial
import subprocess
import time
import os
import re
from datetime import datetime

arduino = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# Configuration
DOWNLOAD_DIR = "D:\\THESIS\\DATASET\\GPHOTO2\\INSECT"
TEMP_DIR = "./temp_photos"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def debug_camera_files():
    """Debug function to see what gphoto2 --list-files actually returns"""
    print("\n[DEBUG] Running gphoto2 --list-files...")
    try:
        result = subprocess.run(["gphoto2", "--list-files"], 
                              capture_output=True, text=True, timeout=15)
        print(f"[DEBUG] Return code: {result.returncode}")
        print(f"[DEBUG] STDOUT:\n{result.stdout}")
        print(f"[DEBUG] STDERR:\n{result.stderr}")
        return result.stdout
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        return None

def get_latest_image_from_camera():
    """Get the filename of the most recently captured image on camera"""
    try:
        stdout = debug_camera_files()
        if not stdout:
            return None
            
        lines = stdout.split('\n')
        image_files = []
        
        print(f"[DEBUG] Processing {len(lines)} lines from gphoto2 output...")
        
        for i, line in enumerate(lines):
            print(f"[DEBUG] Line {i}: {line}")
            if '.ARW' in line.upper() or '.JPG' in line.upper():
                print(f"[DEBUG] Found image line: {line}")
                # Try multiple regex patterns
                patterns = [
                    r'(\w+\.(ARW|JPG|arw|jpg))',
                    r'(DSC\d+\.(ARW|JPG|arw|jpg))',
                    r'([A-Z0-9]+\.(ARW|JPG|arw|jpg))',
                    r'(\S+\.(ARW|JPG|arw|jpg))'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        filename = match.group(1)
                        print(f"[DEBUG] Extracted filename: {filename}")
                        image_files.append(filename)
                        break
        
        print(f"[DEBUG] Found {len(image_files)} image files: {image_files}")
        
        if image_files:
            return image_files[-1]  # Return the last (most recent) file
            
    except Exception as e:
        print(f"[ERROR] Failed to list camera files: {e}")
    
    return None

def test_download_methods(filename):
    """Test different download methods"""
    print(f"[DEBUG] Testing download methods for: {filename}")
    
    methods = [
        # Method 1: Basic get-file
        ["gphoto2", "--get-file", filename],
        # Method 2: Get-file with folder
        ["gphoto2", "--folder", "/", "--get-file", filename],
        # Method 3: Get-file with filename parameter
        ["gphoto2", "--get-file", filename, "--filename", f"./test_{filename}"],
        # Method 4: Get-all-files (downloads everything)
        ["gphoto2", "--get-all-files", "--filename", "./test_%f"]
    ]
    
    for i, method in enumerate(methods):
        print(f"[DEBUG] Trying method {i+1}: {' '.join(method)}")
        try:
            result = subprocess.run(method, capture_output=True, text=True, timeout=30)
            print(f"[DEBUG] Method {i+1} return code: {result.returncode}")
            print(f"[DEBUG] Method {i+1} stdout: {result.stdout}")
            print(f"[DEBUG] Method {i+1} stderr: {result.stderr}")
            
            if result.returncode == 0:
                print(f"[SUCCESS] Method {i+1} worked!")
                return True
        except Exception as e:
            print(f"[DEBUG] Method {i+1} exception: {e}")
    
    return False

def capture_and_debug(angle):
    """Capture image and run full debug"""
    print(f"\n=== DEBUGGING CAPTURE AT {angle} DEGREES ===")
    
    # First, list files before capture
    print("[DEBUG] Files before capture:")
    debug_camera_files()
    
    # Capture image
    print(f"[INFO] Capturing photo at {angle} degrees...")
    try:
        result = subprocess.run(["gphoto2", "--capture-image"], 
                              capture_output=True, text=True, timeout=15)
        print(f"[DEBUG] Capture return code: {result.returncode}")
        print(f"[DEBUG] Capture stdout: {result.stdout}")
        print(f"[DEBUG] Capture stderr: {result.stderr}")
        
        if result.returncode != 0:
            print(f"[ERROR] Capture failed")
            return False
    except Exception as e:
        print(f"[ERROR] Capture failed: {e}")
        return False
    
    # Wait longer for camera to process
    print("[DEBUG] Waiting 3 seconds for camera to process...")
    time.sleep(3)
    
    # List files after capture
    print("[DEBUG] Files after capture:")
    latest_image = get_latest_image_from_camera()
    
    if latest_image:
        print(f"[SUCCESS] Found latest image: {latest_image}")
        # Test download methods
        return test_download_methods(latest_image)
    else:
        print("[ERROR] No image found after capture")
        return False

# Main debug loop - only do a few captures for testing
print("[INFO] Starting DEBUG mode - will only capture 3 photos for testing...")
current_angle = 0
captures_done = 0

while captures_done < 3:  # Only do 3 captures for debugging
    line = arduino.readline().decode().strip()
    if line:
        print(f"[ARDUINO] {line}")
    
    if line == "READY":
        success = capture_and_debug(current_angle)
        
        # Send confirmation back to Arduino regardless
        arduino.write(b"DONE\n")
        arduino.flush()
        print("[INFO] Sent DONE to Arduino")
        
        captures_done += 1
        current_angle += 5
    
    elif line.startswith("X-axis Rotation:"):
        try:
            current_angle = int(line.split(":")[1].strip())
        except:
            pass
    
    elif line == "DONE" or line == "RESET_COMPLETE":
        print("[INFO] Rotation sequence finished.")
        break

print("[INFO] Debug session complete!")
arduino.close()