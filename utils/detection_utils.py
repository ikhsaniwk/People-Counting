# utils/detection_utils.py
import cv2
import numpy as np

def process_detections(frame, model, conf_threshold, frame_skip_id,
                       track_history, counted_ids, scale=1.0):
    """
    Run YOLO detection + tracking, update counts (only person class).
    Returns processed frame and (in_count_increment, out_count_increment).
    """
    results = model.track(frame, persist=True, conf=conf_threshold, verbose=False)

    in_inc, out_inc = 0, 0
    line_x = frame.shape[1] // 2  # garis vertikal tengah

    if results and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)
        classes = results[0].boxes.cls.cpu().numpy().astype(int)  # class ID

        for box, track_id, cls in zip(boxes, track_ids, classes):
            # hanya proses manusia (cls == 0)
            if cls != 0:
                continue

            x1, y1, x2, y2 = box
            cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

            if track_id not in track_history:
                track_history[track_id] = []
            track_history[track_id].append((cx, cy))

            if len(track_history[track_id]) > 10:
                track_history[track_id] = track_history[track_id][-10:]

            # cek crossing
            if len(track_history[track_id]) >= 2:
                prev_x, _ = track_history[track_id][-2]
                curr_x, _ = track_history[track_id][-1]

                if prev_x < line_x and curr_x >= line_x and track_id not in counted_ids:
                    in_inc += 1
                    counted_ids.add(track_id)
                elif prev_x > line_x and curr_x <= line_x and track_id not in counted_ids:
                    out_inc += 1
                    counted_ids.add(track_id)

            # gambar titik putih di pusat objek
            cv2.circle(frame, (cx, cy), 4, (255, 255, 255), -1)

            # tampilkan ID
            cv2.putText(frame, f"ID {track_id}", (cx + 5, cy - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # gambar garis biru tengah
    cv2.line(frame, (line_x, 0), (line_x, frame.shape[0]), (255, 0, 0), 2)

    return frame, (in_inc, out_inc)
