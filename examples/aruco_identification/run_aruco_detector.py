from pathlib import Path
import sys
import cv2

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aruco_identification.aruco_detector import ArucoDetector


def run() -> None:
    detector = ArucoDetector(show_rejected=True, cam_id=0)

    while detector.input_video.isOpened():
        ids, frame = detector.detect()
        cv2.imshow("out", frame)
        key = cv2.waitKey(10)
        if key == 27:
            break

    detector.release()


if __name__ == "__main__":
    run()
