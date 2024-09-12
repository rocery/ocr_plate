import os
from PIL import Image, ImageDraw, ExifTags, UnidentifiedImageError
import cv2
from paddleocr import PaddleOCR
import numpy as np
from .csv_process import data_photo_uploaded, insert_data_ocr_to_csv
from .char_prosess import character_cleaning, character_join
import base64
from io import BytesIO

ocr = PaddleOCR(enable_mkldnn=False, use_tensorrt=False, use_angle_cls=False, use_gpu=False, lang="en", use_direction_classify=True)
folder_upload = 'img_ocr/upload/'
folder_ocr = 'img_ocr/ocr/'
all_csv_data_photo_ocr = 'img_ocr/ocr/all_data_ocr.csv'
csv_data_photo_uploaded = 'img_ocr/upload.csv'
file_extension = None

def img_preprocess(image, action, time_str):
    """
    Preprocess an image and save it to a directory with the given action and time string.
    :param image: PIL image object or file-like object
    :param action: string, either 'masuk' or 'keluar'
    :param time_str: string, format 'YYYY-MM-DD HH:MM:SS'
    :return: numpy array of the image
    """
    if image is None:
        return False

    try:
        # Open image if it's a file-like object, or verify it's already an Image
        if isinstance(image, Image.Image):
            pil_image = image
        else:
            pil_image = Image.open(image)
        
        # Force loading to detect any issues
        pil_image.load()
        
    except UnidentifiedImageError:
        print("UnidentifiedImageError: The file is not a valid image.")
        return False
    except AttributeError as e:
        print(f"AttributeError: {e}")
        return False

    # Split the date and time
    date_part, time_part = time_str.split(' ')
    # Remove the colons from the time part
    time_part = time_part.replace(':', '')
    
    # Save image in "folder_upload/date/
    folder_uploaded = folder_upload + date_part + '/'
    
    # Check folder_upload
    if not os.path.exists(folder_uploaded):
        os.makedirs(folder_uploaded)
    
    # Extract the file extension
    global file_extension
    file_extension = os.path.splitext(image.filename)[1]
    
    # Construct the new filename with time_str
    filename = f"{os.path.splitext(image.filename)[0]}-{date_part} {time_part}{file_extension}"
    
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
    
    # Save the image
    original_path = os.path.join(folder_uploaded, filename)
    pil_image.save(original_path)
    
    # Read the image
    image = cv2.imread(original_path)
    
    # Update the CSV
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
        
        global plat
        plat = []

        for data in txts:
            cleaned_string = character_cleaning(data)
            plat.append(cleaned_string)
        
        plat = character_join(plat)
        
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

def numpy_to_base64(image_np):
    # Convert NumPy array to PIL Image
    pil_image = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
    
    # Save the PIL image to a BytesIO buffer
    buffer = BytesIO()
    pil_image.save(buffer, format="JPEG")
    
    # Encode the image to base64
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/jpeg;base64,{img_str}"

def save_image_ocr(image, datetime, no_mobil, action):
    # Split the date and time
    date_part, time_part = datetime.split(' ')
    # Remove the colons from the time part
    time_part = time_part.replace(':', '')
    
    # Make CSV File Name based on Date
    csv = f"{date_part}.csv"
    
    # Result /img_ocr/ocr/Date
    folder_path = os.path.join(folder_ocr, date_part)
    # Result /img_ocr/ocr/Date/{date}.scv
    csv_path_date = os.path.join(folder_path, csv)
    csv_path_all = os.path.join(folder_ocr, "all_ocr.csv")
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    global file_extension
    # B123CA_Masuk_20240515_121231.jpg
    file_name = f"{no_mobil}_{action}_{date_part}_{time_part}{file_extension}"
    # /img_ocr/ocr/Date/B123CA_Masuk_20240515_121231.jpg
    img_path = os.path.join(folder_path, file_name)
    
    insert_data_ocr_to_csv(csv_path_date, csv_path_all, img_path, no_mobil, action, datetime)
    
    cv2.imwrite(img_path, image)