from pathlib import Path
import sys
import cv2

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aruco_identification.aruco_detector import ArucoDetector
from aruco_identification.mqtt_aruco_detector import ArucoMQTTService, GROUP_ID, CAM_ID


def run() -> None:
    detector = ArucoDetector(show_rejected=True, cam_id=CAM_ID)
    aruco_service = ArucoMQTTService(detector=detector, id=GROUP_ID)
    aruco_service.start()

    while True:
        ids, frame = detector.detect()
        cv2.imshow("out", frame)
        key = cv2.waitKey(10)
        if key == 27:
            break

    print("Stopping Aruco MQTT service.")
    aruco_service.stop()
    detector.release()


if __name__ == "__main__":
    run()
