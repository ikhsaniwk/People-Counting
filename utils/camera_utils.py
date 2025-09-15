# utils/camera_utils.py
import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CameraStream:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.latest_frame = None
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        if self.running:
            return True
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Camera index {self.camera_index} cannot be opened")
                return False
            # set some properties if supported
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            self.running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logger.info(f"Camera {self.camera_index} started (capture thread running)")
            return True
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            return False

    def _capture_loop(self):
        while self.running and self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                # sleep briefly to avoid busy loop
                time.sleep(0.05)
                continue
            with self.lock:
                # store latest frame (BGR)
                self.latest_frame = frame
            # small sleep to yield CPU
            time.sleep(0.005)

    def read(self):
        """Return the latest frame (or None). Non-blocking."""
        with self.lock:
            if self.latest_frame is None:
                return None
            # return a copy to avoid races
            return self.latest_frame.copy()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        logger.info("CameraStream stopped")
