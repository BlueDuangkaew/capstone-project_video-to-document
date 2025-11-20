import cv2
import numpy as np
import os

class FrameChangeDetector:
    def __init__(self, threshold=30, blur_size=(5, 5)):
        self.threshold = threshold
        self.blur_size = blur_size

    def detect_changes(self, video_path, output_dir):
        os.makedirs(output_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        prev_frame = None
        frame_idx = 0
        change_idx = 0

        change_frames = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, self.blur_size, 0)

            if prev_frame is not None:
                diff = cv2.absdiff(gray, prev_frame)
                score = np.mean(diff)

                if score > self.threshold:
                    ts = frame_idx / fps
                    filename = os.path.join(output_dir, f"change_{change_idx:04d}_{ts:.2f}s.jpg")
                    cv2.imwrite(filename, frame)

                    change_frames.append({
                        "frame_path": filename,
                        "timestamp": ts,
                        "score": score
                    })

                    change_idx += 1

            prev_frame = gray
            frame_idx += 1

        cap.release()

        return change_frames
