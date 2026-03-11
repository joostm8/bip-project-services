from pathlib import Path
import os
import platform
import cv2
import yaml

from aruco_identification.aruco_detector import ArucoDetector


def load_config(config_file: Path) -> dict:
    with open(config_file, "r", encoding="utf-8") as file_handle:
        config = yaml.safe_load(file_handle)
    return config or {}


def is_preview_available() -> bool:
    system = platform.system().lower()
    if system == "linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


def parse_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def run(config_path = None) -> None:
    config = load_config(config_path)
    cam_cfg = config.get("cam", {})
    cam_id = int(cam_cfg.get("cam_id", 0))
    cam_name = cam_cfg.get("cam_name")
    preview_requested = parse_bool(cam_cfg.get("preview"), default=True)

    if platform.system().lower() == "linux" and cam_name:
        detector = ArucoDetector(show_rejected=True, video_source=cam_name)
    else:
        detector = ArucoDetector(show_rejected=True, cam_id=cam_id)

    preview_enabled = preview_requested and is_preview_available()
    if not preview_requested:
        print("Preview disabled by configuration, running in headless mode.")
    elif not preview_enabled:
        print("No display detected, running in headless mode.")

    try:
        while detector.input_video.isOpened():
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
        detector.release()


if __name__ == "__main__":
    run("../config.yaml")
