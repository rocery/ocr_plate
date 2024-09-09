import csv
import os

def data_photo_uploaded(csv_file_path, photo_path, time_upload, action):
    # Check if the file exists; if not, create it and write the header
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['photo_path', 'time_upload', 'category'])
    
    # Append the new row to the CSV file
    with open(csv_file_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([photo_path, time_upload, action])
        
def read_data_csv():
    data = []
    file_path = '../img_ocr/ocr/all_data_ocr.csv'

    # Membaca data dari file ocr.csv
    with open(file_path, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        header = next(csvreader)  # Skip the header row
        for row in csvreader:
            data.append(row)
            
    # Ambil 100 data terbaru
    recent_data = data[-100:]
    
    # Tambahkan nomor urut secara menurun
    numbered_data = [[i + 1, *row] for i, row in enumerate(recent_data[::-1])]

    return numbered_data