from pathlib import Path
import sys
import cv2
import yaml

from aruco_identification.aruco_detector import ArucoDetector
from aruco_identification.mqtt_aruco_detector import ArucoMQTTService


def load_config(config_file: Path) -> dict:
    with open(config_file, "r", encoding="utf-8") as file_handle:
        config = yaml.safe_load(file_handle)
    return config or {}


def run(config_path = None) -> None:
    config = load_config(config_path)
    cam_id = int(config.get("cam", {}).get("cam_id", 0))

    detector = ArucoDetector(show_rejected=True, cam_id=cam_id)
    aruco_service = ArucoMQTTService(detector=detector, id=cam_id, config_path=str(config_path))
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
    run("../config.yaml")
