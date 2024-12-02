import torch
from PIL import Image
import cv2
from transformers import OwlViTProcessor, OwlViTForObjectDetection

def detect_license_plate(image_np, model_name="google/owlvit-base-patch32", text_queries=None, threshold=0.2):
    if text_queries is None:
        text_queries = ["car license plate", "vehicle registration plate"]

    # Convert the NumPy array to a PIL image
    image = Image.fromarray(image_np)

    # Load the OWL-ViT model and processor
    model = OwlViTForObjectDetection.from_pretrained(model_name)
    processor = OwlViTProcessor.from_pretrained(model_name)

    # Preprocess the image and text queries
    inputs = processor(images=image, text=text_queries, return_tensors="pt")

    # Perform inference
    with torch.no_grad():
        outputs = model(**inputs)

    # Extract bounding boxes and scores
    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process(outputs, target_sizes=target_sizes)

    # Get the bounding boxes, labels, and scores
    boxes = results[0]["boxes"]
    scores = results[0]["scores"]

    # Filter boxes by the given score threshold
    filtered_boxes = boxes[scores > threshold]

    # Check if the number of detected license plates is 0 or more than 1
    num_boxes = len(filtered_boxes)
    if num_boxes == 0:
        raise ValueError("No license plates detected with the given threshold.")
    elif num_boxes > 1:
        raise ValueError("More than one license plate detected. Please provide an image with only one license plate.")

    # Since there should only be one box, we can process it directly
    xmin, ymin, xmax, ymax = map(int, filtered_boxes[0])

    # Adjust the ymax to get 3/4 of the height from the top
    height = ymax - ymin
    ymax = ymin + int(0.72 * height)

    # Crop the image based on the adjusted bounding box
    cropped_image_np = image_np[ymin:ymax, xmin:xmax]
    cv2.imwrite("img_ocr/temp/licence_plate.png", cropped_image_np)

    # Return the cropped image as a NumPy array
    return cropped_image_np