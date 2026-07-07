import logging
import cv2
import time
import os  # Added to handle directory creation and paths
from fast_alpr import ALPR

# -----------------------------
# CONFIG
# -----------------------------
OUTPUT_DIR = "Output_images"     # Directory to store saved vehicle images
ACCURACY_THRESHOLD = 0.93        # 93% minimum accuracy requirement
STREAK_REQUIRED = 3              # Plate must be found at 93%+ for 3 straight frames
COOLDOWN_DURATION = 5.0          # Buffer time in seconds between scans
ALLOWED_PLATE_LENGTHS = (9, 11)  # Plate must be exactly 9 or 10 characters long

# Ensure the output directory exists right away
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Suppress INFO logs from the underlying open_image_models package
logging.getLogger("open_image_models").setLevel(logging.WARNING)

# -----------------------------
# Load Model (fast_alpr)
# -----------------------------
alpr = ALPR(
    detector_model="yolo-v9-t-384-license-plate-end2end",
    ocr_model="cct-xs-v2-global-model",
)

# -----------------------------
# Camera Setup
# -----------------------------
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("Could not open camera.")
    exit()

print("Camera Started")
print("Press Q to Quit")

# Track the exact timestamp when the camera is allowed to scan again
cooldown_until = 0.0

# Tracks consecutive frames where a highly accurate plate was seen
plate_streak_counter = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Create a copy of the frame to draw on for the display window
    display_frame = frame.copy()
    
    valid_plate_detected = False
    current_time = time.time()

    # Variables to preserve the confirmed plate details for the text log file
    confirmed_plate_number = ""
    confirmed_avg_accuracy = 0.0

    # -------------------------------------------------
    # Detection Block (Skipped if within the 5s cooldown)
    # -------------------------------------------------
    if current_time >= cooldown_until:
        alpr_results = alpr.predict(frame)
        
        highest_frame_accuracy = 0.0
        best_plate_this_frame = ""

        for result in alpr_results:
            # Extract plate text and calculate average character confidence
            confidences = result.ocr.confidence
            avg_accuracy = sum(confidences) / len(confidences) if confidences else 0.0
            plate_number = result.ocr.text
            
            if avg_accuracy > highest_frame_accuracy:
                highest_frame_accuracy = avg_accuracy
                best_plate_this_frame = plate_number

            # Extract bounding box from the detection payload
            bbox = result.detection.bounding_box
            x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)

            # Draw box and text on display screen
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                display_frame,
                f"{plate_number} ({avg_accuracy:.2%})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        # Streak logic check: If a plate was seen with 93%+ accuracy this frame
        if highest_frame_accuracy >= ACCURACY_THRESHOLD:
            plate_streak_counter += 1
            print(f"Confidence threshold met! Streak count: {plate_streak_counter}/{STREAK_REQUIRED}")
            
            # Keep track of the values to write if the streak hits its limit
            confirmed_plate_number = best_plate_this_frame
            confirmed_avg_accuracy = highest_frame_accuracy
        else:
            # If the plate disappears or drops below 93%, reset the frame counter
            plate_streak_counter = 0

        # Trigger ONLY if the high confidence streak requirement has been fully met
        if plate_streak_counter >= STREAK_REQUIRED:
            
            # Validates that the string length is EITHER 9 or 10 characters
            if len(confirmed_plate_number) in ALLOWED_PLATE_LENGTHS:
                valid_plate_detected = True
            else:
                print(f"Ignored invalid plate length: {confirmed_plate_number} ({len(confirmed_plate_number)} chars). Resetting streak.")
                plate_streak_counter = 0  # Break streak and scan next frame immediately without cooldown

    else:
        # Reset the streak tracker while the camera cooldown is active
        plate_streak_counter = 0
        
        # Calculate remaining time for the on-screen visual alert
        remaining = cooldown_until - current_time
        cv2.putText(
            display_frame,
            f"Cooldown Active ({remaining:.1f}s)",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 165, 255),  # Orange text
            2
        )

    # -------------------------------------------------
    # Display the current frame
    # -------------------------------------------------
    cv2.imshow("ANPR Camera", display_frame)

    # -------------------------------------------------
    # Trigger Logic (Saves data and handles cooldown)
    # -------------------------------------------------
    if valid_plate_detected:
        print(f"Verified valid plate ({len(confirmed_plate_number)} chars)! Writing {confirmed_plate_number} to log file...")

        # Generate a dynamic timestamp name string (e.g., 20231024_153045_ABC123DE.jpg)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        image_filename = f"{timestamp}_{confirmed_plate_number}.jpg"
        image_path = os.path.join(OUTPUT_DIR, image_filename)

        # 1. Save the clean unannotated image reference snapshot file
        cv2.imwrite(image_path, frame)

        # 2. Append the plate text metadata information safely into records.txt
        with open("records.txt", "a") as f:
            f.write(f"{image_filename}\t{confirmed_plate_number}\t{confirmed_avg_accuracy:.2%}\n")

        # 3. Visual notification feedback directly over the live monitor stream
        cv2.putText(
            display_frame,
            "Saved to Log!",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        cv2.imshow("ANPR Camera", display_frame)
        cv2.waitKey(1)  # Force immediate window update

        # 4. Initiate your 5-second scanner protection freeze window counter
        plate_streak_counter = 0
        cooldown_until = time.time() + COOLDOWN_DURATION
        print(f"Cooldown initiated for {COOLDOWN_DURATION} seconds. Resuming stream view...")

    # Break out of loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
