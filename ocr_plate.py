from flask import Flask, render_template, request, flash, redirect, url_for, session
from PIL import Image
import time
from script.ocr_process import ocr_predict, img_preprocess
from script.licence_plate_detector import detect_license_plate

app = Flask(__name__)
app.secret_key = 'itbekasioke'
USER_SECRET_KEY = 'user123'

@app.route('/ocr/login_ocr', methods=['GET', 'POST'])
def login_ocr():
    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        if secret_key == USER_SECRET_KEY:
            session['authenticated'] = True
            return redirect(url_for('ocr'))
        else:
            flash('Password salah, silahkan coba kembali.', 'danger')
    
    return render_template('login.html')

message = None
message_type = None
time_str = None
img_extension = None

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    if not session.get('authenticated'):
        return redirect(url_for('login_ocr'))

    if request.method == 'POST':
        action = request.form['action']
        image = request.files['image']
        
        if image:
            try:
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                
                image = img_preprocess(image, action, time_str)
                
                # Detect licence plate
                try:
                    image = detect_license_plate(image)
                except:
                    message = 'Tidak Terdeteksi Plat Nomor Pada Gambar. Silahkan Ulangi Proses Upload. Error Code: 0x1'
                    message_type = 'danger'
                    flash(message, message_type)
                    return render_template('ocr.html', message=message, message_type=message_type)
                
                ocr_result = ocr_predict(image)
                
                if ocr_result == False:
                    message = 'Tidak Terdeteksi Angka/Huruf Pada Foto. Silahkan Ulangi Proses Upload. Error Code: 0x2'
                    message_type = 'danger'
                    render_template('ocr.html', message=message, message_type=message_type)
            
            except (IOError, SyntaxError):
                message = 'Foto Yang Diupload Salah, Silahkan Ulangi Proses Upload. Error 0x4'
                message_type = 'danger'
                return render_template('ocr.html', message=message, message_type=message_type)
            
    return render_template('ocr.html')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
    )