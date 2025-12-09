# libcamera Integration Plan

## Overview
This document outlines the steps required to integrate libcamera into the current repository, replacing the existing OpenCV and PiCamera implementations.

## Current Camera Setup
- **OpenCV (cv2)**: Used for computer vision tasks
- **PiCamera**: Used for video streaming
- **Custom camera abstraction**: Implemented in `base_camera.py` and `camera_opencv.py`

## Required Changes

### ~~1. server/camera_opencv.py~~
- ~~Replace `cv2.VideoCapture` with libcamera~~
- ~~Update frame capture logic~~
- ~~Update camera initialization and configuration~~
- ~~Maintain compatibility with the existing Camera class interface~~

### 2. server/FPV.py
- Replace `picamera.PiCamera` with libcamera
- Update frame capture logic
- Update camera configuration
- Maintain the streaming functionality

### 3. server/base_camera.py
- Update to support libcamera interface
- Ensure the threading model remains functional
- Maintain the CameraEvent and frame access interface

### 4. server/app.py
- Update Camera initialization
- Update frame generation logic
- Ensure compatibility with the Flask application

### 5. server/webServer.py
- Update camera usage in the main logic
- Ensure the video feed route works with the new camera implementation

## Implementation Steps

1. **Start with server/FPV.py** as it's the most direct video capture component
2. **Update server/camera_opencv.py** to use the new video capture method
3. **Update server/base_camera.py** to support the new interface
4. **Update server/app.py** to use the updated camera
5. **Update server/webServer.py** to use the updated camera

## Key Considerations

1. **Backward Compatibility**: The new implementation should maintain the same interface as the existing code
2. **Performance**: Ensure the new implementation maintains or improves video streaming performance
3. **Error Handling**: Implement robust error handling for camera initialization and frame capture
4. **Thread Safety**: Ensure the threading model works correctly with the new camera implementation

## Tools Required
- libcamera-dev
- python3-libcamera
- updated dependencies for the new camera implementation

## Next Steps
1. Verify libcamera installation
2. Start with updating FPV.py
3. Test the video stream functionality
4. Gradually update the other components