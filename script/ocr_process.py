import os
from PIL import Image, ImageDraw, ExifTags
import cv2
from csv_process import data_photo_uploaded
from paddleocr import PaddleOCR

ocr = PaddleOCR(enable_mkldnn=False, use_tensorrt=False, use_angle_cls=False, use_gpu=False, lang="en", use_direction_classify=True)
folder_upload = 'img_ocr/upload/'
csv_data_photo_uploaded = 'img_ocr/upload.csv'

def img_preprocess(image, action, time_str):
    
    # Split the date and time
    date_part, time_part = time_str.split(' ')
    # Remove the colons from the time part
    time_part = time_part.replace(':', '')
    
    folder_upload = folder_upload + date_part + ' ' + time_part + '/'
    
    # Check folder_upload
    if not os.path.exists(folder_upload):
        os.makedirs(folder_upload)
    
    # Extract the file extension
    file_extension = os.path.splitext(image.filename)[1]
    
    # Construct the new filename with time_str
    filename = f"{os.path.splitext(image.filename)[0]}-{time_str}{file_extension}"
    
    # Open the image with PIL to handle EXIF data and save later
    pil_image = Image.open(image.stream)
    
    # Rotate image if needed based on EXIF orientation
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = pil_image._getexif()
        if exif is not None:
            orientation = exif.get(orientation, 1)
            if orientation == 3:
                pil_image = pil_image.rotate(180, expand=True)
            elif orientation == 6:
                pil_image = pil_image.rotate(270, expand=True)
            elif orientation == 8:
                pil_image = pil_image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Handle cases where the image doesn't have EXIF data
        pass
    
    original_path = os.path.join(folder_upload, filename)
    pil_image.save(original_path)
    
    image = cv2.imread(original_path)
    data_photo_uploaded(csv_data_photo_uploaded, original_path, time_str, action)
    return image

def ocr_predict(frame):
    try:
        # Perform OCR using PaddleOCR
        try:
            result = OCR.ocr(frame, cls=True) 
        except:
            OCR = PaddleOCR(enable_mkldnn=False, use_tensorrt=False, use_angle_cls=False, use_gpu=False, lang="en", use_direction_classify=True)
            result = OCR.ocr(frame, cls=False)
        
        # Check if result is None
        if result is None:
            raise ValueError("OCR result is None. Please check the input image and OCR settings.")

        # Sort the OCR results based on the x-coordinate of the top-left corner (left to right)
        sorted_result = sorted(result[0], key=lambda x: x[0][0][0])

        # Extract the bounding boxes, texts, and confidence scores from the sorted result
        boxes = [line[0] for line in sorted_result]
        txts = [line[1][0] for line in sorted_result]
        scores = [line[1][1] for line in sorted_result]
        
        # boxes_result = [line[0] for line in result]
        
        # print("BR: {}".format(boxes_result))
        # print("B : {}".format(boxes))

        reject = []
        global plat
        plat = []
        for data in txts:
            if any(char in data for char in reject) or data[0] == '0':
                continue
            else:
                cleaned_string = character_cleaning(data)
                plat.append(cleaned_string)
            print(f"Data: {data}, cleaned string: {cleaned_string}")

        print(f"Plat: {plat}")
        plat = character_process(plat)
        print(f"OCR: {plat}")

        # Convert boxes to the required format
        boxes = [np.array(box, dtype=np.int32).reshape((-1, 1, 2)) for box in boxes]

        return [(box, txt, score) for box, txt, score in zip(boxes, txts, scores)]

    except Exception as e:
        print(f"Error during OCR: {e}")
        return False

def fixed_colors():
    """Return a fixed set of colors."""
    return [(0, 0, 255), (255, 0, 0), (0, 0, 127), (63, 0, 127), (4, 38, 82)]

def show_labels(frame, predictions):
    pil_image = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil_image)
    
    colors = fixed_colors()
    
    for box, txt, score in predictions:
        color = colors[np.random.randint(0, len(colors))]
        
        # Draw bounding box (using the points from PaddleOCR)
        cv2.polylines(frame, [box], isClosed=True, color=color, thickness=2)
        
        # Calculate the position to put the text (top-left corner of the bounding box)
        x, y = box[0][0]
        
        # Overlay text and score on the image
        text = f'{txt} ({score:.2f})'
        cv2.putText(frame, text, (x - 3, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, text, (x - 3, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    
    del draw
    opencvimage = np.array(frame)
    # global plat
    return opencvimage, plat