import numpy as np
import cv2
import streamlit as st
import requests
from PIL import Image
import json
from typing import List, Dict
from dotenv import load_dotenv
import os
import time
from pathlib import Path

# Get the current working directory
dir = Path(os.getcwd())

# Load environment variables from .env file
ENV_PATH = dir / '.env'
load_dotenv(ENV_PATH)

# Get API URL from environment variables
API_URL = os.environ["API_URL"]
BEARER_TOKEN = os.environ["BEARER_TOKEN"]

st.title('Ring Virtual Try On')

# Initialize session state if not already done
# if "gender_selected" not in st.session_state:
if "ring_selected" not in st.session_state:
    # st.session_state.gender_selected = False
    st.session_state.ring_selected = False
    st.session_state.finger_selected = False
    st.session_state.fingers_detected = []
    st.session_state.finger_to_coords = {}  # Store finger data for each selection

# # Gender Selection
# if not st.session_state.gender_selected:
#     gender = st.selectbox("Select Gender", ["Men", "Women"])
#     if st.button("Next"):
#         st.session_state.gender = gender
#         st.session_state.gender_selected = True

# Define ring options based on gender
# if st.session_state.gender_selected:
if not st.session_state.ring_selected:
    rings = {
        "Ring 1": "rings/men/men-ring-02.png",
        "Ring 2": "rings/men/men-ring-03.png",
        "Ring 3": "rings/women/RFSV015D1F.png",
        "Ring 4": "rings/women/RFSV016D1F.png"
        }
        
    # Display ring images with "Try On" buttons
    for name, image_path in rings.items():
        try:
            obj = Image.open(image_path).convert("RGBA")
        except Exception as e:
            st.error(f"Error loading image {image_path}: {e}")
            continue
            
        st.image(obj, caption=name, width=200)
            
        if st.button(f"Try On {name}"):
            st.session_state.ring_selected = True
            st.session_state.selected_ring = name
            st.session_state.object = obj
            break  # Exit the loop after a ring is selected

else:
    # Capture Hand Image and Overlay Selected Ring
    object = st.session_state.object

    # Display selected Ring
    st.image(object, caption="Selected Ring", width=200)

    # Provide options to either upload or capture an image
    option = st.radio("Choose Image Source", ("Capture Image", "Upload Image"))

    if option == "Capture Image":
        # Streamlit widget to capture an image using the webcam
        camera_image = st.camera_input("Capture an image of the wrist")
        if camera_image is not None:
            with open(dir / "temp_image_cam.jpg", "wb") as f:
                f.write(camera_image.getbuffer())
            img_path = str(dir / 'temp_image_cam.jpg')

    elif option == "Upload Image":
        # Streamlit widget to upload an image
        uploaded_image = st.file_uploader("Upload an image of the wrist", type=["jpg", "jpeg", "png"])
        if uploaded_image is not None:
            with open(dir / "temp_image.jpg", "wb") as f:
                f.write(uploaded_image.getbuffer())
            img_path = str(dir / 'temp_image.jpg')

    # Proceed if either a camera or uploaded image is available
    if (option == "Capture Image" and camera_image) or (option == "Upload Image" and uploaded_image):
        start = time.time()
                
        payload = {}
        files = [
            ('image', (img_path, open(img_path, 'rb'), 'image/jpeg'))
        ]
        headers = {
            'Authorization': f"Bearer {BEARER_TOKEN}"
        }
        response = requests.post(API_URL, headers = headers, data = payload, files = files, verify = False)
        end = time.time() - start
        st.write(f"Time taken for API call: {end} seconds")

        # Parsing API Response
        results = response.text

        try:
            data = json.loads(results)
            st.session_state.fingers_detected = [finger for finger in ["Index", "Middle", "Ring", "Pinky"] if finger in data["results"]]
            st.session_state.finger_to_coords = data["results"]  # Store all finger data

            num_fingers = len(st.session_state.fingers_detected)
            st.write(f"Detected {num_fingers} finger(s): {', '.join(st.session_state.fingers_detected)}")
        except requests.RequestException as e:
            st.error(f"Error with API request or processing response: {e}")
            st.write("Here's the response text:")
            st.write(results)
        except json.JSONDecodeError:
            st.write("Error decoding JSON. Here's the response text:")
            st.write(results)  # Display raw response text
            st.error("Failed to decode JSON from the API response.")
            st.stop()
        except KeyError:
            st.write("Error: Expected data format is not present in the response.")
            st.write("Here's the response text:")
            st.write(results)  # Display raw response text
            st.error("Failed to find expected 'wrist' data in the API response.")
            st.stop()

        # Load and display the uploaded image
        try:
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            st.image(img, width=200)

            my_img = img.copy()
            my_img1 = img.copy()
            updated_img = img.copy()
        except Exception as e:
            st.error(f"Error decoding image: {e}")

        # Default to the first detected finger
        if not st.session_state.finger_selected:
            if len(st.session_state.fingers_detected) > 1:
                selected_finger = st.selectbox("Select Finger", st.session_state.fingers_detected)
            else:
                selected_finger = st.session_state.fingers_detected[0]

            if st.button("Next"):
                st.session_state.finger = selected_finger
                st.session_state.finger_selected = True

        if st.session_state.finger_selected:
            # Clear previous overlay
            img_with_ring = Image.fromarray(img, "RGB").convert("RGBA")

            # Continue with the selected finger
            selected_finger = st.session_state.finger
            finger_data = st.session_state.finger_to_coords[selected_finger]

            # Extract coordinates
            left_coords: List[float] = finger_data["left"]
            right_coords: List[float] = finger_data["right"]
            center_coords: List[float] = finger_data["center"]
            rotation_angle: float = finger_data["rotation_angle"]
            polygon_coords = finger_data["polygon"]

            center_coords_rev: List[float] = [(left_coords[0] + right_coords[0]) / 2, (left_coords[1] + right_coords[1]) / 2]
            img_height, img_width = img.shape[:2]
            left_pixel = (int(left_coords[0] * img_width), int(left_coords[1] * img_height))
            right_pixel = (int(right_coords[0] * img_width), int(right_coords[1] * img_height))
            center_pixel = (int(center_coords_rev[0] * img_width), int(center_coords_rev[1] * img_height))

            # Create an image for the overlay
            overlay = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))

            # Draw circles at the new coordinates
            cv2.circle(img, left_pixel, 2, (0, 0, 255), -1)
            cv2.circle(img, center_pixel, 2, (0, 0, 255), -1)
            cv2.circle(img, right_pixel, 2, (0, 0, 255), -1)

            polygon_pixels = [(int(coord[0] * img_width / 100), int(coord[1] * img_height / 100)) for coord in polygon_coords]
            cv2.polylines(img, [np.array(polygon_pixels)], isClosed=True, color=(0, 255, 0), thickness=1)

            st.image(img, caption='Wrist with Coordinates and polygon', use_column_width=True)

            # Calculate finger length in pixels
            f_length = np.sqrt((right_pixel[0] - left_pixel[0]) ** 2 + (right_pixel[1] - left_pixel[1]) ** 2)

            # Resize ring image to match finger length
            try:
                object_np = np.array(object)
                ring_width = object_np.shape[1]
                resize_factor = f_length / ring_width
                new_width = int(ring_width * resize_factor)
                new_height = int(object_np.shape[0] * resize_factor)
                object_resized = cv2.resize(object_np, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            except Exception as e:
                st.error(f"Error resizing ring image: {e}")

            # Rotate the resized ring to align with finger angle
            angle = 180 - rotation_angle
            st.write('Finger rotation angle:', rotation_angle)
            st.write('Rotation matrix angle:', angle)

            try:
                rotation_matrix = cv2.getRotationMatrix2D((new_width // 2, new_height // 2), angle, 1.0)
                object_rotated = cv2.warpAffine(object_resized, rotation_matrix, (new_width, new_height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
            except Exception as e:
                st.error(f"Error rotating ring image: {e}")

            # Convert the rotated ring back to PIL image for overlay
            object_rotated_pil = Image.fromarray(object_rotated, "RGBA")

            # Calculate the position to place the ring
            center_x = (left_pixel[0] + right_pixel[0]) // 2
            center_y = (left_pixel[1] + right_pixel[1]) // 2
            top_left_x = int(center_x - new_width // 2)
            top_left_y = int(center_y - new_height // 2)

            # Ensure the ring fits within the image bounds
            top_left_x = max(top_left_x, 0)
            top_left_y = max(top_left_y, 0)
            bottom_right_x = min(top_left_x + new_width, img_width)
            bottom_right_y = min(top_left_y + new_height, img_height)

            # Paste the resized and rotated ring on the overlay image
            overlay.paste(object_rotated_pil, (top_left_x, top_left_y), object_rotated_pil)

            # Combine the original image with the overlay
            img_with_ring = Image.alpha_composite(Image.fromarray(img, "RGB").convert("RGBA"), overlay)

            st.image(img_with_ring, caption='Ring Overlay with coordinates and polygon', use_column_width=True)

            # Combine the original image with the overlay
            my_img_with_ring = Image.alpha_composite(Image.fromarray(my_img, "RGB").convert("RGBA"), overlay)

            st.image(my_img_with_ring, caption='Ring Overlay', use_column_width=True)

            # Provide an option to change the finger
            if len(st.session_state.fingers_detected) > 1:
                new_finger = st.selectbox("Change Finger", st.session_state.fingers_detected)
                if st.button("Update Overlay"):
                    st.session_state.finger = new_finger
                    finger_data = st.session_state.finger_to_coords[new_finger]

                    # Recalculate coordinates and update ring overlay
                    left_coords = finger_data["left"]
                    right_coords = finger_data["right"]
                    center_coords = finger_data["center"]
                    rotation_angle = finger_data["rotation_angle"]
                    polygon_coords = finger_data["polygon"]

                    center_coords_rev = [(left_coords[0] + right_coords[0]) / 2, (left_coords[1] + right_coords[1]) / 2]
                    img_height, img_width = updated_img.shape[:2]
                    left_pixel = (int(left_coords[0] * img_width), int(left_coords[1] * img_height))
                    right_pixel = (int(right_coords[0] * img_width), int(right_coords[1] * img_height))
                    center_pixel = (int(center_coords_rev[0] * img_width), int(center_coords_rev[1] * img_height))

                    # Clear previous overlay
                    img_with_ring = Image.fromarray(updated_img, "RGB").convert("RGBA")

                    # Draw circles at the new coordinates
                    cv2.circle(updated_img, left_pixel, 2, (0, 0, 255), -1)
                    cv2.circle(updated_img, center_pixel, 2, (0, 0, 255), -1)
                    cv2.circle(updated_img, right_pixel, 2, (0, 0, 255), -1)
                    
                    polygon_pixels = [(int(coord[0] * img_width / 100), int(coord[1] * img_height / 100)) for coord in polygon_coords]
                    cv2.polylines(updated_img, [np.array(polygon_pixels)], isClosed=True, color=(0, 255, 0), thickness=1)

                    st.image(updated_img, caption='Updated finger with Coordinates and polygon', use_column_width=True)

                    # Recalculate finger length in pixels
                    f_length = np.sqrt((right_pixel[0] - left_pixel[0]) ** 2 + (right_pixel[1] - left_pixel[1]) ** 2)

                    # Resize ring image to match new finger length
                    try:
                        object_np = np.array(object)
                        ring_width = object_np.shape[1]
                        resize_factor = f_length / ring_width
                        new_width = int(ring_width * resize_factor)
                        new_height = int(object_np.shape[0] * resize_factor)
                        object_resized = cv2.resize(object_np, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
                    except Exception as e:
                        st.error(f"Error resizing ring image: {e}")

                    # Rotate the resized ring to align with new finger angle
                    angle = 180 - rotation_angle
                    st.write('New Finger rotation angle:', rotation_angle)
                    st.write('New Rotation matrix angle:', angle)

                    try:
                        rotation_matrix = cv2.getRotationMatrix2D((new_width // 2, new_height // 2), angle, 1.0)
                        object_rotated = cv2.warpAffine(object_resized, rotation_matrix, (new_width, new_height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
                    except Exception as e:
                        st.error(f"Error rotating ring image: {e}")

                    # Convert the rotated ring back to PIL image for overlay
                    object_rotated_pil = Image.fromarray(object_rotated, "RGBA")

                    # Calculate the position to place the ring
                    center_x = (left_pixel[0] + right_pixel[0]) // 2
                    center_y = (left_pixel[1] + right_pixel[1]) // 2
                    top_left_x = int(center_x - new_width // 2)
                    top_left_y = int(center_y - new_height // 2)

                    # Ensure the ring fits within the image bounds
                    top_left_x = max(top_left_x, 0)
                    top_left_y = max(top_left_y, 0)
                    bottom_right_x = min(top_left_x + new_width, img_width)
                    bottom_right_y = min(top_left_y + new_height, img_height)

                    # Create a new overlay image to remove previous ring
                    overlay = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
                    overlay.paste(object_rotated_pil, (top_left_x, top_left_y), object_rotated_pil)

                    # Combine the original image with the new overlay
                    img_with_ring = Image.alpha_composite(Image.fromarray(updated_img, "RGB").convert("RGBA"), overlay)

                    st.image(img_with_ring, caption='Updated Ring Overlay with coordinates and polygon', use_column_width=True)


                    # Combine the original image with the new overlay
                    my_img_with_ring = Image.alpha_composite(Image.fromarray(my_img1, "RGB").convert("RGBA"), overlay)

                    st.image(my_img_with_ring, caption='Updated Ring Overlay', use_column_width=True)
