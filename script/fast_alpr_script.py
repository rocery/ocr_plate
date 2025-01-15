from fast_alpr import ALPR
import cv2
alpr = ALPR(
    detector_model="yolo-v9-t-384-license-plate-end2end",
    ocr_model="global-plates-mobile-vit-v2-model"
)
def fast_alpr_process(image):
    # Load the image using OpenCV
    # image = cv2.imread(image_path)
    
    print(image)
    
    if image is None:
        raise ValueError(f"Unable to load image at path: {image}")
    
    # Initialize the ALPR model
    
    
    # Perform ALPR prediction
    fast_alpr_result = alpr.predict(image)
    
    # Validate the result
    if len(fast_alpr_result) != 1:
        return False
    
    fast_alpr_data = []
    
    for data in fast_alpr_result:
        # Get detection confidence
        detection_confidence = data.detection.confidence
        # Get bounding box
        bounding_box = data.detection.bounding_box
        # Get OCR text
        ocr_text = data.ocr.text

        fast_alpr_data.append(round(detection_confidence, 2) * 100)
        fast_alpr_data.append(bounding_box.x1)
        fast_alpr_data.append(bounding_box.y1)
        fast_alpr_data.append(bounding_box.x2)
        fast_alpr_data.append(bounding_box.y2)
        fast_alpr_data.append(ocr_text)
    
    # Extract bounding box coordinates
    x1, y1, x2, y2 = fast_alpr_data[1], fast_alpr_data[2], fast_alpr_data[3], fast_alpr_data[4]
    
    # Ensure bounding box coordinates are within image dimensions
    height, width, _ = image.shape
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(width, int(x2)), min(height, int(y2))
    
    # Crop the image
    cropped_image = image[y1:y2, x1:x2]
    cv2.imwrite("../img_ocr/temp/licence_plate_try.png", cropped_image)
    
    return fast_alpr_data

# # Test the function
# print(fast_alpr_process("a.jpeg"))

# a = cv2.imread("a.jpeg")

# print(fast_alpr_process(a))
