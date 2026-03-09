import cv2
import platform

# Linux makes it much simpler: 
# just run
# v4l2-ctl --list-devices
# and note down the right device and the /dev/videoX 


def returnCameraIndexes():
    system = platform.system().lower()
    api_preference = cv2.CAP_DSHOW if system == "windows" else cv2.CAP_V4L2 if system == "linux" else cv2.CAP_ANY

    # checks the first 10 indexes.
    index = 0
    arr = []
    i = 10
    while i > 0:
        cap = cv2.VideoCapture(index, api_preference)
        if cap.read()[0]:
            arr.append(index)
            cap.release()
        index += 1
        i -= 1
    return arr

print(returnCameraIndexes())