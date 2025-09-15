# config/settings.py
class Config:
    """Configuration class for People Counting System"""
    
    def __init__(self):
        self.CAM_INDEX = 1
        self.MODEL_PATH = "yolov8n.pt"
        self.FRAME_SKIP = 2
        self.CONF_THRESHOLD = 0.5
        self.SCALE = 1.0
        self.FRAME_MODE = 1  # 1: normal, 2: grayscale, 3: edge, 4: heatmap
        self.IS_RUNNING = False
        # counts
        self.IN_COUNT = 0
        self.OUT_COUNT = 0
