# aruco_detector.py
import platform

import cv2

class ArucoDetector:

    def __init__(self, cam_id=0, video_source=None, show_rejected=False):
        """
        Initialize the Aruco detector with a camera or video source.
        
        :param cam_id: Camera ID to use if no video source is provided.
        :param video_source: Optional path to a video file. If None, the camera will be used.
        :param show_rejected: Boolean flag to indicate if rejected markers should be displayed.
        """
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.detector_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.detector_params)

        # Video capture setup
        self.video_source = video_source if video_source is not None else cam_id
        api_preference = self._get_api_preference(self.video_source)
        self.input_video = cv2.VideoCapture(self.video_source, api_preference)

        # Keep focus fixed across platforms so the camera locks to the same point.
        # Some cameras require autofocus to be disabled before manual focus takes effect.
        self.input_video.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.input_video.set(cv2.CAP_PROP_FOCUS, 150)
        self.show_rejected = show_rejected


        # Timing and iteration tracking
        self.total_time = 0
        self.total_iterations = 0
        self.wait_time = 0 if video_source else 10

        if not self.input_video.isOpened():
            raise Exception("Error: Could not open video source.")

    def _get_api_preference(self, source):
        """Select a backend that works on both Windows and Linux camera devices."""
        system = platform.system().lower()

        # Device indices and /dev/videoX should use native camera backends.
        if isinstance(source, int):
            if system == "windows":
                return cv2.CAP_DSHOW
            if system == "linux":
                return cv2.CAP_V4L2
            return cv2.CAP_ANY

        if isinstance(source, str) and source.startswith("/dev/video"):
            return cv2.CAP_V4L2 if system == "linux" else cv2.CAP_ANY

        # File/stream inputs should use automatic backend selection.
        return cv2.CAP_ANY

    def detect(self):
        """
        Detects Aruco markers in a frame from the video or camera.
        
        :return: A tuple (ids, frame) where ids is a list of detected marker IDs and frame is the annotated image.
        """
        ret, frame = self.input_video.read()
        if not ret:
            return None, None
        
        # Start timer for detection performance measurement
        tick = cv2.getTickCount()

        # Detect markers
        corners, ids, rejected = self.detector.detectMarkers(frame)

        # Calculate processing time for this frame
        current_time = (cv2.getTickCount() - tick) / cv2.getTickFrequency()
        self.total_time += current_time
        self.total_iterations += 1

        # Print mean detection time every 30 iterations
        if self.total_iterations % 30 == 0:
            print(f"Detection Time = {current_time * 1000:.2f} ms (Mean = {1000 * self.total_time / self.total_iterations:.2f} ms)")
            if ids is not None:
                print(f"Detected markers: {[i for id in ids for i in id]}")
            # also print focus distance (so I can set it manually later)
            print(self.input_video.get(cv2.CAP_PROP_FOCUS))
        # Annotate frame with detected markers
        frame_copy = frame.copy()
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame_copy, corners, ids)

        # Optionally, show rejected markers
        if self.show_rejected and len(rejected) > 0:
            cv2.aruco.drawDetectedMarkers(frame_copy, rejected, borderColor=(100, 0, 255))

        # Return detected IDs and the annotated frame
        return ids, frame_copy

    def release(self):
        """
        Releases the video capture and closes any OpenCV windows.
        """
        self.input_video.release()
        cv2.destroyAllWindows()