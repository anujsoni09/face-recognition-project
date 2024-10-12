# Real-Time Face Recognition Web App
## Overview

[![N|Solid](https://miro.medium.com/v2/resize:fit:640/1*dKU4uBSnJCs4jzkkuiALoQ.png)]()


This project is a real-time face recognition web application that utilizes Flask as the backend framework, alongside Dlib and OpenCV for face detection and recognition. The application provides an interactive user interface built with HTML, CSS, and JavaScript, allowing users to capture and recognize faces in real time.
# Table of Contents
- Features
- Technologies Used
- Installation

## Features

- Real-time face detection and recognition
- User-friendly web interface
- Capture images using webcam
- Lightweight and efficient

## Technologies Used
#### Frontend:
- HTML
- CSS
-  JavaScript
#### Backend:
- Flask
#### Libraries:
- Dlib (for face detection and recognition)
- OpenCV (for image processing)

## Installation
Follow the steps below to set up the project locally:

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/real-time-face-recognition.git
    cd real-time-face-recognition
    ```

2. Create a virtual environment:

    ```sh
    python -m venv myenv
    source myenv/bin/activate  # On Windows use `myenv\Scripts\activate`
    ```
3. Install the dlib packages and required packages:

    ```sh
    python -m pip install dlib-19.24.1-cp311-cp311-win_amd64.whl
    pip install -r requirements.txt
    ```
4. Run the application:
    ```sh
    python server.py
    ```
    
## Usage
Allow the web app to access your webcam.
The application will automatically detect faces in real time.
When a face is recognized, the app will display the name of the person.
