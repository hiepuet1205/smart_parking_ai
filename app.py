import cv2
import numpy as np
import easyocr
import base64
from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO
import imutils
from functools import reduce
import re

# Khởi tạo Flask app
app = Flask(__name__)

# Hàm xử lý Base64 để chuyển thành ảnh
def decode_base64_image(image_base64):
    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data)).convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

# Hàm xử lý nhận diện biển số
def process_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
    # edged = cv2.Canny(bfilter, 30, 200)

    thresh = cv2.adaptiveThreshold(
      gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    keypoints = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(imutils.grab_contours(keypoints), key=cv2.contourArea, reverse=True)[:10]

    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break

    if location is None:
        return {"error": "No plate region detected"}

    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [location], 0, 255, -1)
    new_image = cv2.bitwise_and(image, image, mask=mask)

    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2 + 1, y1:y2 + 1]

    reader = easyocr.Reader(['en'])
    results = reader.readtext(cropped_image)

    detected_texts = []
    for (_, text, confidence) in results:
        detected_texts.append({"text": text, "confidence": confidence})

    result = reduce(
      lambda acc, text: acc + " " + re.sub(r'[^A-Za-z0-9-]', '', text["text"]), 
      detected_texts, 
      "" 
    )

    return {"result": result}

# Endpoint API
@app.route('/detect', methods=['POST'])
def detect():
    try:
        # Lấy dữ liệu từ request
        data = request.json
        image_base64 = data.get("image")
        if not image_base64:
            return jsonify({"error": "No image provided"}), 400

        # Giải mã Base64 và xử lý ảnh
        image = decode_base64_image(image_base64)
        result = process_image(image)

        # Trả kết quả
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Chạy server
if __name__ == '__main__':
    app.run(debug=True)
