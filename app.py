from flask import Flask, render_template,request,jsonify
from PIL import Image
import base64
from yolo_implementation import YOLOImplementation
from model import run_model
import io


app = Flask(__name__)

videoPaths = [
    "static/vids/23712-337108764_medium.mp4",
    "static/vids/cars.mp4",
    "static/ids/23712-337108764_medium.mp4",
    "static/vids/cars.mp4"
]

maskPaths = [
    "static/masks/vid1.png",
    'static/masks/vid2.png',
    "static/masks/vid1.png",
    "static/masks/vid2.png"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    data = request.get_json()
    image_data = data['image']

    header, base64_str = image_data.split(',', 1)

    image_bytes = base64.b64decode(base64_str)
    image = Image.open(io.BytesIO(image_bytes))

    # (Optional) Save image for verification
    image.save("received_frame.jpg")

    # Here you can call YOLO model and do processing
    print("Received frame for YOLO processing")

    # next_video_index = (current_video_index + 1) % len(videoPaths)

    yolo = YOLOImplementation()
    dict = yolo.execute(videoPaths[0], maskPaths[0], 0)
    prediction = run_model(dict)
    print(prediction)

    return jsonify({"status": "frame received","prediction":prediction})

if __name__ == '__main__':
    app.run(debug=True,port=8080)
