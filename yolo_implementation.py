
import numpy as np
from ultralytics import YOLO
import cvzone
import cv2


model = YOLO('Yolo-Weights/yolov8l.pt')

class YOLOImplementation:
    def __init__(self):
        self.classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
                      "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
                      "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
                      "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
                      "baseball bat",
                      "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
                      "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
                      "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
                      "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
                      "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
                      "teddy bear", "hair drier", "toothbrush"
                      ]

        self.d = {'car': 0, 'truck': 0, 'bus': 0, 'motorbike': 0}

    def execute(self, video, mask_image, time):

        # clip = VideoFileClip(video)
        # duration = ceil(clip.duration)

        cap = cv2.VideoCapture(video)
        mask = cv2.imread(mask_image)

        frame_counter = 0

        fps = cap.get(cv2.CAP_PROP_FPS)   
        specific_time = int(fps * time)

        while True:
            success, img = cap.read()
            if frame_counter == specific_time:
                imregion = cv2.bitwise_and(img, mask)
                dets = np.empty((0, 5))
                results = model(imregion, stream=True)
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        w, h = x2 - x1, y2 - y1

                        conf = int(box.conf[0] * 100) / 100
                        cls = int(box.cls[0])
                        currentClass = self.classNames[cls]
                        print(f'{currentClass}:{conf}')
                        if currentClass in ['car', 'truck', 'bus', 'motorbike'] and conf > .3:
                            self.d[currentClass] += 1
                            cvzone.putTextRect(img, f"{currentClass}: {conf}", (x1, y1), thickness=0, scale=1)
                            currntArray = np.array([x1, y1, x2, y2, conf])
                            # cvzone.cornerRect(img, (x1, y1, w, h), l=7, rt=5)
                            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            dets = np.vstack((dets, currntArray))
                # cv2.imshow('Image', img)
                # print(signal_time)

                # cv2.waitKey(0)
                return self.d
                # return self.d


            frame_counter += 1

            # cv2.imshow('Image', img)
            # print(signal_time)
            # cv2.waitKey(1)



# obj = YOLOImplementation()
# d = obj.execute('/Users/akashzamnani/Desktop/Python-Project/CarDetection/videos/23712-337108764_medium.mp4','new_vid_trial.png',5)
# print(d)