# Ring Virtual Try-On Application

This project is a web application built using Streamlit that allows users to virtually try on rings. The app guides users through selecting a gender, choosing a ring from a set of options, capturing an image of their hand, and overlaying the selected ring onto the image of their chosen finger. The ring is aligned with the finger's coordinates and rotation angle to provide a realistic preview.

## Features

- Gender Selection: Users can choose between "Men" and "Women" to filter available ring options.
- Ring Selection: Users can browse through a set of rings specific to the selected gender and choose a ring to try on.
- Finger Selection: Users can choose the finger (Index, Middle, Ring, or Pinky) on which they want to try the ring.
- Hand Image Capture: Users can capture an image of their hand using their webcam.
- Ring Overlay: The app calculates the appropriate size and angle to overlay the selected ring on the captured hand image, providing a realistic preview.
- Results Display: The app displays the final image with the ring overlaid, both with and without the reference coordinates.

## Dependencies

The project requires the following libraries:

- numpy
- opencv-python
- streamlit
- requests
- Pillow

## To install the dependencies, use the following command:

pip install -r requirements.txt

Running the App

1. Clone the repository to your local machine:

   git clone https://github.com/nishi-v/ring_virtual_tryon.git

2. Navigate to the project directory:

   cd ring-virtual-try-on

3. Install the required packages:

   pip install -r requirements.txt

4. Run the Streamlit app:

   streamlit run hand_cap.py

5. Open the provided URL in your web browser to access the app.

## How It Works

1. Gender Selection: Users start by selecting their gender, which determines the ring options displayed in the next step.
2. Ring Selection: Users are shown images of rings specific to the selected gender. Upon selecting a ring, they proceed to the next step.
3. Finger Selection: Users choose which finger they want to place the ring on. This choice is sent to an API that provides the coordinates and rotation angle for the selected finger.
4. Image Capture: The user captures an image of their hand using their webcam. This image is then processed to overlay the selected ring.
5. Ring Overlay: The app uses the coordinates and rotation angle provided by the API to accurately size and position the ring on the selected finger.
6. Final Display: The app displays the hand image with the ring overlaid, both with and without the reference coordinates.

## API Integration

The app integrates with an external API to obtain the finger's coordinates and rotation angle. 

The captured hand image is sent to the endpoint, and the response is used to overlay the selected ring accurately.
