import cv2
import os

# Create directory to save markers
output_dir = "aruco_markers"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Define the dictionary to use for Aruco markers (e.g., 6x6_250 has 250 possible markers)
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# Set the size for the markers
marker_size = 700  # 700x700 pixels

# Generate 25 markers
for marker_id in range(25):
    # Create the marker image
    marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
    
    # Save the marker as an image file
    marker_filename = os.path.join(output_dir, f"aruco_marker_{marker_id}.png")
    cv2.imwrite(marker_filename, marker_image)

    print(f"Saved Aruco marker ID {marker_id} at {marker_filename}")

print("All 25 Aruco markers have been generated and saved.")
