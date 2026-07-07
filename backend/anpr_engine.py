import time
import os
import threading
import traceback
import subprocess
import json
import numpy as np
import signal
from fast_alpr import ALPR
from backend.state import add_log, add_recent_event

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
import cv2

OUTPUT_DIR = "Output_images"
ACCURACY_THRESHOLD = 0.93
STREAK_REQUIRED = 3
COOLDOWN_DURATION = 5.0
ALLOWED_PLATE_LENGTHS = (9, 10, 11)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def get_stream_resolution(rtsp_url):
    """
    Queries the resolution of the RTSP stream using ffprobe.
    Returns (width, height) on success, or None on failure.
    """
    cmd = [
        "ffprobe",
        "-rtsp_transport", "tcp",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        "-timeout", "5000000",  # 5 seconds in microseconds
        rtsp_url
    ]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5.0
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            if streams:
                width = streams[0].get("width")
                height = streams[0].get("height")
                if width and height:
                    return int(width), int(height)
    except Exception as e:
        print(f"Error querying resolution with ffprobe: {e}")
    return None


class ANPREngine:
    def __init__(self):
        self.alpr = ALPR(
            detector_model="yolo-v9-t-384-license-plate-end2end",
            ocr_model="cct-xs-v2-global-model",
        )

        # RTSP Camera URL
        self.rtsp_url = "rtsp://admin:12345@192.168.1.20:554/main.asp"

        # FFmpeg process, frame storage, and sync primitives
        self.process = None
        self.latest_decoded_frame = None
        self.frame_ready_event = threading.Event()
        self.frame_lock = threading.Lock()
        
        # Determined dynamically before starting FFmpeg decoder
        self.width = None
        self.height = None

        self.cooldown_until = 0.0
        self.plate_streak_counter = 0
        self.current_frame = None
        self.is_running = False

    def get_frame(self):
        """Returns the current JPEG encoded frame for the MJPEG stream"""
        if self.current_frame is not None:
            ret, buffer = cv2.imencode('.jpg', self.current_frame)
            if ret:
                return buffer.tobytes()
        return None

    def start(self):
        self.is_running = True
        # Start camera reader thread
        threading.Thread(target=self._camera_reader_loop, daemon=True).start()
        # Start main processing loop thread
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _read_exact(self, stream, n):
        """
        Reads exactly n bytes from the input stream.
        Returns bytes or None if EOF/disconnected.
        """
        data = bytearray()
        while len(data) < n:
            try:
                chunk = stream.read(n - len(data))
                if not chunk:
                    return None
                data.extend(chunk)
            except Exception as e:
                print(f"Socket read error: {e}")
                return None
        return bytes(data)

    def _cleanup_process(self):
        """Terminates and reaps the FFmpeg subprocess to prevent zombie processes."""
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            except Exception as e:
                print(f"Error cleaning up FFmpeg process: {e}")
            finally:
                self.process = None

    def _camera_reader_loop(self):
        """
        Continuously retrieves resolution via ffprobe, launches FFmpeg subprocess,
        and reads raw BGR24 frames to store them as self.latest_decoded_frame.
        """
        while self.is_running:
            # 1. Resolve Stream Resolution
            add_log("Attempting to connect to RTSP stream...", "info")
            resolution = get_stream_resolution(self.rtsp_url)
            if not resolution:
                add_log("Could not retrieve RTSP stream resolution. Retrying in 5 seconds...", "error")
                for _ in range(50):
                    if not self.is_running:
                        return
                    time.sleep(0.1)
                continue

            self.width, self.height = resolution
            add_log(f"RTSP stream resolution detected: {self.width}x{self.height}", "success")
            
            # 2. Launch FFmpeg Subprocess
            cmd = [
                "ffmpeg",
                "-rtsp_transport", "tcp",
                "-fflags", "nobuffer",
                "-flags", "low_delay",
                "-i", self.rtsp_url,
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-"
            ]
            
            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=0
                )
                add_log("FFmpeg decoder pipeline started.", "success")
            except Exception as e:
                add_log(f"Failed to start FFmpeg subprocess: {e}", "error")
                for _ in range(50):
                    if not self.is_running:
                        return
                    time.sleep(0.1)
                continue

            # 3. Read Frames continuously
            frame_size = self.width * self.height * 3
            
            while self.is_running:
                raw_frame = self._read_exact(self.process.stdout, frame_size)
                if raw_frame is None:
                    add_log("FFmpeg stream disconnected or process exited.", "warning")
                    break

                try:
                    frame = np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
                    
                    with self.frame_lock:
                        self.latest_decoded_frame = frame
                    
                    self.frame_ready_event.set()
                except Exception as e:
                    print(f"Error decoding raw video frame: {e}")
                    break

            # Cleanup FFmpeg process
            self._cleanup_process()
            
            if self.is_running:
                add_log("RTSP stream disconnected. Reconnecting in 5 seconds...", "warning")
                for _ in range(50):
                    if not self.is_running:
                        return
                    time.sleep(0.1)

    def _run_loop(self):
        while self.is_running:
            try:
                # Wait for a new frame to be ready (timeout lets us check self.is_running periodically)
                self.frame_ready_event.wait(timeout=1.0)
                if not self.is_running:
                    break
                
                if not self.frame_ready_event.is_set():
                    continue
                
                with self.frame_lock:
                    self.frame_ready_event.clear()
                    frame = self.latest_decoded_frame
                
                if frame is None:
                    continue

                display_frame = frame.copy()
                valid_plate_detected = False
                current_time = time.time()

                confirmed_plate_number = ""
                confirmed_avg_accuracy = 0.0

                if current_time >= self.cooldown_until:
                    alpr_results = self.alpr.predict(frame)
                    
                    highest_frame_accuracy = 0.0
                    best_plate_this_frame = ""

                    for result in alpr_results:
                        confidences = result.ocr.confidence
                        avg_accuracy = sum(confidences) / len(confidences) if confidences else 0.0
                        plate_number = result.ocr.text
                        
                        if avg_accuracy > highest_frame_accuracy:
                            highest_frame_accuracy = avg_accuracy
                            best_plate_this_frame = plate_number

                        bbox = result.detection.bounding_box
                        x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)

                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(display_frame, f"{plate_number} ({avg_accuracy:.2%})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    if highest_frame_accuracy >= ACCURACY_THRESHOLD:
                        self.plate_streak_counter += 1
                        # Only log streak sporadically to avoid spamming the logs
                        if self.plate_streak_counter == 1 or self.plate_streak_counter == STREAK_REQUIRED:
                            add_log(f"Confidence threshold met! Streak count: {self.plate_streak_counter}/{STREAK_REQUIRED}", "info")
                        
                        confirmed_plate_number = best_plate_this_frame
                        confirmed_avg_accuracy = highest_frame_accuracy
                    else:
                        self.plate_streak_counter = 0

                    if self.plate_streak_counter >= STREAK_REQUIRED:
                        if len(confirmed_plate_number) in ALLOWED_PLATE_LENGTHS:
                            valid_plate_detected = True
                        else:
                            add_log(f"Ignored invalid plate length: {confirmed_plate_number} ({len(confirmed_plate_number)} chars).", "warning")
                            self.plate_streak_counter = 0

                else:
                    self.plate_streak_counter = 0
                    remaining = self.cooldown_until - current_time
                    cv2.putText(display_frame, f"Cooldown Active ({remaining:.1f}s)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

                self.current_frame = display_frame

                if valid_plate_detected:
                    add_log(f"Verified valid plate ({len(confirmed_plate_number)} chars)! Processing {confirmed_plate_number}...", "success")
                    
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    image_filename = f"{timestamp}_{confirmed_plate_number}.jpg"
                    image_path = os.path.join(OUTPUT_DIR, image_filename)

                    cv2.imwrite(image_path, frame)

                    with open("records.txt", "a") as f:
                        f.write(f"{image_filename}\t{confirmed_plate_number}\t{confirmed_avg_accuracy:.2%}\n")
                    
                    # Call the real business logic processor
                    from backend.supabase_client import process_plate_event
                    
                    def run_processor(plate, conf, img):
                        try:
                            result = process_plate_event(
                                plate_number=plate,
                                confidence=conf,
                                camera_name="Gate 1",
                                image_url=img
                            )
                            
                            action = result.get("action")
                            if action == "cooldown_skipped":
                                add_log(result.get("message", "Cooldown active"), "warning")
                            elif action == "error":
                                add_log(f"DB Error: {result.get('message')}", "error")
                            else:
                                vehicle = result.get("vehicle")
                                v_name = vehicle["owner_name"] if vehicle else "Guest"
                                direction = "IN" if action == "entry_created" else "OUT"
                                
                                event_data = {
                                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "plate_number": plate,
                                    "confidence": conf,
                                    "direction": direction,
                                    "vehicle_name": v_name,
                                    "local_image_path": img
                                }
                                
                                # Update in-memory state and SSE for the UI dashboard
                                add_recent_event(event_data)
                                add_log(f"Success: {action.replace('_', ' ').title()} for {plate}", "success")
                        except Exception as e:
                            err = f"Database processing error: {e}"
                            print(err)
                            add_log(err, "error")
 
                    threading.Thread(
                        target=run_processor,
                        args=(confirmed_plate_number, confirmed_avg_accuracy, image_path),
                        daemon=True
                    ).start()

                    cv2.putText(display_frame, "Saved to Log!", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    self.current_frame = display_frame

                    self.plate_streak_counter = 0
                    self.cooldown_until = time.time() + COOLDOWN_DURATION
                    add_log(f"Cooldown initiated for {COOLDOWN_DURATION} seconds.", "info")

            except Exception as e:
                error_msg = f"Camera loop crash prevented: {e}"
                print(error_msg)
                traceback.print_exc()
                add_log(error_msg, "error")
                time.sleep(1.0) # Prevent tight spin

    def stop(self):
        self.is_running = False
        self.frame_ready_event.set()
        self._cleanup_process()


anpr_engine = ANPREngine()
