from pathlib import Path
import os
import platform
import cv2
import yaml

from aruco_identification.aruco_detector import ArucoDetector
from aruco_identification.mqtt_aruco_detector import ArucoMQTTService


def load_config(config_file: Path) -> dict:
    with open(config_file, "r", encoding="utf-8") as file_handle:
        config = yaml.safe_load(file_handle)
    return config or {}


def is_preview_available() -> bool:
    system = platform.system().lower()
    if system == "linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True

def run(config_path = None) -> None:
    config = load_config(config_path)
    cam_cfg = config.get("cam", {})
    cam_id = int(cam_cfg.get("cam_id", 0))
    cam_name = cam_cfg.get("cam_name")
    preview_requested = cam_cfg.get("preview", True)

    if platform.system().lower() == "linux" and cam_name:
        detector = ArucoDetector(show_rejected=True, video_source=cam_name)
    else:
        detector = ArucoDetector(show_rejected=True, cam_id=cam_id)

    preview_enabled = preview_requested and is_preview_available()
    if not preview_requested:
        print("Preview disabled by configuration, running in headless mode.")
    elif not preview_enabled:
        print("No display detected, running in headless mode.")

    aruco_service = ArucoMQTTService(detector=detector, id=cam_id, config_path=str(config_path))
    aruco_service.start()

    try:
        while True:
            ids, frame = detector.detect()
            if frame is None:
                continue

            if preview_enabled:
                try:
                    cv2.imshow("out", frame)
                    key = cv2.waitKey(10)
                    if key == 27:
                        break
                except cv2.error as error:
                    preview_enabled = False
                    print(f"Display output unavailable, switching to headless mode: {error}")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        print("Stopping Aruco MQTT service.")
        aruco_service.stop()
        detector.release()


if __name__ == "__main__":
    run(config_path = "cam-config.yaml")
