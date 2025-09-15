# main.py
import time
import logging
import os
import threading
import queue

from flask import Flask, Response, render_template, jsonify

# local modules
from config.settings import Config as SettingsConfig
from utils.camera_utils import CameraStream
from utils.detection_utils import process_detections
from db.local_database import init_db, insert_count, get_summary, get_last_records
from ultralytics import YOLO

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load global config
settings = SettingsConfig()

# Shared runtime state
cap_stream = None  # CameraStream instance
model = None
track_history = {}
counted_ids = set()
frame_id = 0
fps = 0.0
prev_time = 0.0

# Buffer for streaming (MJPEG)
FRAME_BUFFER_SIZE = 3
frame_buffer = queue.Queue(maxsize=FRAME_BUFFER_SIZE)

# Lock for counts
counts_lock = threading.Lock()


def init_model():
    global model
    try:
        model = YOLO(settings.MODEL_PATH)
        model.to("cpu")
        logger.info(f"Model loaded: {settings.MODEL_PATH}")
        return True
    except Exception as e:
        logger.error(f"Model load error: {e}")
        return False


def start_camera():
    global cap_stream
    if cap_stream is None:
        cap_stream = CameraStream(settings.CAM_INDEX)
        ok = cap_stream.start()
        return ok
    return True


def stop_camera():
    global cap_stream
    if cap_stream:
        cap_stream.stop()
        cap_stream = None


def inference_thread():
    """
    Background thread: ambil frame dari CameraStream,
    jalankan YOLO detection, update counter, simpan ke DB, dan push frame ke buffer.
    """
    global frame_id, fps, prev_time, model, track_history, counted_ids

    logger.info("Inference thread started")
    while True:
        if not settings.IS_RUNNING or cap_stream is None or model is None:
            time.sleep(0.05)
            continue

        frame = cap_stream.read()
        if frame is None:
            time.sleep(0.02)
            continue

        # hitung fps
        current_time = time.time()
        if prev_time:
            fps = 0.9 * fps + 0.1 * (1.0 / (current_time - prev_time))
        prev_time = current_time
        frame_id += 1

        # hanya proses setiap FRAME_SKIP
        if frame_id % settings.FRAME_SKIP == 0:
            try:
                processed_frame, (in_inc, out_inc) = process_detections(
                    frame,
                    model,
                    conf_threshold=settings.CONF_THRESHOLD,
                    frame_skip_id=frame_id,
                    track_history=track_history,
                    counted_ids=counted_ids,
                    scale=settings.SCALE
                )
            except Exception as e:
                logger.exception(f"Error during detection: {e}")
                processed_frame = frame
                in_inc, out_inc = 0, 0

            if in_inc or out_inc:
                with counts_lock:
                    settings.IN_COUNT += in_inc
                    settings.OUT_COUNT += out_inc

                    # simpan ke DB
                    if in_inc > 0:
                        for _ in range(in_inc):
                            insert_count("IN")
                    if out_inc > 0:
                        for _ in range(out_inc):
                            insert_count("OUT")
        else:
            processed_frame = frame

        # encode dan push ke buffer
        try:
            import cv2
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                if frame_buffer.full():
                    try:
                        frame_buffer.get_nowait()
                    except queue.Empty:
                        pass
                try:
                    frame_buffer.put_nowait(frame_bytes)
                except queue.Full:
                    pass
        except Exception as e:
            logger.exception(f"Error encoding frame: {e}")

        time.sleep(0.01)


# Flask routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    def generate():
        boundary = b'--frame\r\n'
        while True:
            try:
                frame = frame_buffer.get(timeout=1.0)
                yield boundary + b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
            except queue.Empty:
                import numpy as np
                import cv2
                blank = 255 * np.ones((10, 10, 3), dtype=np.uint8)
                ret, buf = cv2.imencode('.jpg', blank)
                yield boundary + b'Content-Type: image/jpeg\r\n\r\n' + (buf.tobytes() if ret else b'') + b'\r\n'
            except GeneratorExit:
                break
            except Exception as e:
                logger.exception(f"Error in video_feed generator: {e}")
                break
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stats')
def stats():
    with counts_lock:
        in_count = settings.IN_COUNT
        out_count = settings.OUT_COUNT
    return jsonify({
        'in_count': in_count,
        'out_count': out_count,
        'fps': round(fps, 1),
        'running': settings.IS_RUNNING
    })


@app.route('/db_summary')
def db_summary():
    """Endpoint untuk ringkasan jumlah IN dan OUT dari database"""
    return jsonify(get_summary())


@app.route('/db_last')
def db_last():
    """Endpoint untuk melihat 10 data terakhir dari database"""
    return jsonify(get_last_records(10))


@app.route('/start', methods=['POST'])
def start():
    if not start_camera():
        return jsonify({'status': 'camera_failed'}), 500
    if model is None and not init_model():
        return jsonify({'status': 'model_failed'}), 500

    settings.IS_RUNNING = True
    logger.info("System started")
    return jsonify({'status': 'started'})


@app.route('/stop', methods=['POST'])
def stop():
    settings.IS_RUNNING = False
    logger.info("System stopped")
    return jsonify({'status': 'stopped'})


@app.route('/reset', methods=['POST'])
def reset():
    with counts_lock:
        settings.IN_COUNT = 0
        settings.OUT_COUNT = 0
    counted_ids.clear()
    track_history.clear()
    logger.info("Counter reset")
    return jsonify({'status': 'reset'})


@app.route('/test')
def test():
    return "✅ Flask is working! Test endpoint reached."


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

    logger.info("Starting People Counting Web Server...")

    # init database
    init_db()

    if not start_camera():
        logger.error("Failed to start camera. Exiting.")
    elif not init_model():
        logger.error("Failed to load model. Exiting.")
    else:
        inf_thread = threading.Thread(target=inference_thread, daemon=True)
        inf_thread.start()
        app.run(host='0.0.0.0', port=5000, threaded=True)
