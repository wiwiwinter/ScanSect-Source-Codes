import serial
import subprocess

# Adjust serial port (e.g., COM3 for Windows, /dev/ttyACM0 for WSL/Linux)
arduino = serial.Serial('/dev/ttyACM0', 115200)

photo_counter = 0

while True:
    line = arduino.readline().decode().strip()
    if line == "CAPTURE":
        photo_counter += 1
        print(f"[INFO] Capturing photo {photo_counter}...")

        subprocess.run([
            "gphoto2",
            "--capture-image"
        ])

        # Optional handshake back to Arduino
        # arduino.write(b"DONE\n")

        if photo_counter >= 61:  # after full revolution
            print("[INFO] Capture complete.")
            break
