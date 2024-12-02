import re

def character_cleaning(data):
    len_data = len(data)
    result = []
    
    if len_data == 0:
        pass
    
    elif type(data) is not list or len_data == 1:
        txt = ''.join([char for char in data if not char.islower() and char != ' '])
        txt = re.sub(r'[^A-Z0-9]', '', data)
        result.append(txt)
        return result
    
    else:
        for text in data:
            txt = ''.join([char for char in text if not char.islower() and char != ' '])
            txt = re.sub(r'[^A-Z0-9]', '', text)
            
            if txt != '':
                result.append(txt)
                
        return result

def character_join(data):
    if type(data) is not list:
        return data
    
    else:
        data = [item for sublist in data for item in sublist]
        data = ''.join(data)
        return data

def character_check(data):
    # Regex pattern: ^[A-Za-z]{1,2}\d{1,4}[A-Za-z]{1,3}$
    # print(data)
    data_ = advanced_license_plate_correction(data)
    # print(data_)
    pattern = r'^[A-Z]{1,2}(?!0)\d{1,4}[A-Z]{1,3}$'
    if re.match(pattern, data_):
        return True, data_
    else:
        return False, data
   

def advanced_license_plate_correction(ocr_result):
    # Aturan koreksi karakter
    digit_corrections = {
        '8': 'B',   # Delapan menjadi B
        # '5': 'S'    # Lima menjadi S
    }
    
    # Koreksi khusus untuk huruf
    letter_corrections = {
        '1': 'I',   # Satu menjadi I
        '0': 'O',   # Nol menjadi O
        # '5': 'S'    # Lima menjadi S
    }
    
    def correct_plate_format(plate):
        # Pola plat nomor: 1-2 huruf, diikuti digit (tidak dimulai 0), 1-4 digit, 1-3 huruf
        pattern = r'^[A-Z]{1,2}(?!0)\d{1,4}[A-Z]{1,3}$'
        
        # Koreksi karakter
        corrected_plate = ''
        
        # Koreksi huruf pertama
        if not plate[0].isalpha():
            corrected_plate = 'B'
        else:
            corrected_plate = plate[0]
        
        # Koreksi digit
        digit_part = ''
        for char in plate[1:-3]:
            if char.isdigit():
                corrected_char = digit_corrections.get(char, char)
                digit_part += corrected_char
        
        # Tambahkan digit yang sudah dikoreksi
        corrected_plate += digit_part
        
        # Koreksi huruf terakhir
        letter_part = plate[-3:]
        corrected_letter_part = ''
        for char in letter_part:
            if char.isdigit():
                # Koreksi digit menjadi huruf pada bagian huruf
                corrected_char = letter_corrections.get(char, char).upper()
                corrected_letter_part += corrected_char
            elif char.isalpha():
                corrected_letter_part += char.upper()
        
        # Tambahkan huruf terakhir yang sudah dikoreksi
        corrected_plate += corrected_letter_part
        
        # Validasi dengan pola
        if re.match(pattern, corrected_plate):
            return corrected_plate
        
        # Fallback jika tidak valid
        return plate
    
    return correct_plate_format(ocr_result)