from flask import Flask, render_template, request, flash, redirect, url_for, session
import time
from script.ocr_process import ocr_predict, img_preprocess, show_labels, numpy_to_base64
from script.licence_plate_detector import detect_license_plate
from script.char_prosess import character_check
from script.sql_db import get_ekspedisi, get_kendaraan_ga, masuk_223

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
label = None
data = None
status_kendaraan_ga = None
ekspedisi = None
time_ = None
date_ = None
csv_data = None

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    if not session.get('authenticated'):
        return redirect(url_for('login_ocr'))

    if request.method == 'POST':
        # csv_data = read_data_csv()
        action = request.form['action']
        image = request.files['image']
        
        if image:
            try:
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                time_ = time.strftime("%H:%M:%S", time.localtime())
                date_ = time.strftime("%Y-%m-%d", time.localtime())
                
                image = img_preprocess(image, action, time_str)
                
                # Detect licence plate
                try:
                    image = detect_license_plate(image)
                except:
                    message = 'Tidak Terdeteksi Plat Nomor Pada Gambar. Silahkan Ulangi Proses Upload. Error Code: 0x1'
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type)
                
                ocr_result = ocr_predict(image)
                
                if ocr_result == False:
                    message = 'Tidak Terdeteksi Angka/Huruf Pada Foto. Silahkan Ulangi Proses Upload. Error Code: 0x2'
                    message_type = 'danger'
                    render_template('ocr.html', message=message, message_type=message_type)
                
                show_label = show_labels(image, ocr_result)
                label = show_label[1]
                data = numpy_to_base64(show_label[0])
                
                if character_check(label) == False:
                    message = 'Plat Nomor Terbaca Salah. Mohon Ulangion Proses Upload. Error Code: 0x3'
                    message_type = 'danger'
                    render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                
                status_kendaraan_ga = get_kendaraan_ga(label)
                ekspedisi = get_ekspedisi(label)

                # # Test
                # message = 'Plat Nomor: {}.'.format(label)
                # message_type = 'success'
                # render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                # return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                
            except (IOError, SyntaxError):
                message = 'Foto Yang Diupload Salah, Silahkan Ulangi Proses Upload. Error 0x4'
                message_type = 'danger'
                return render_template('ocr.html', message=message, message_type=message_type)
        
        if action == 'Masuk':
            print("Plat Nomor : {}".format(label))
            print("Data Gambar: {}".format(type(data)))
            last_loc = None
            
            if status_kendaraan_ga == True:
                last_loc = masuk_223(date_, label, time_, 'security', 'GA')
                print(last_loc)
                print(status_kendaraan_ga)
                if last_loc == 'masuk':
                    message = 'Kendaraan: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                else:
                    message = 'Kendaraan: {} Berhasil Masuk.'.format(label)
                    message_type = 'success'
                    return render_template('ocr.html',
                                           message=message,
                                           message_type=message_type,
                                           data=data,
                                           label=label,
                                           type='GA',
                                           action=action)
            
            elif ekspedisi:
                last_loc = masuk_223(date_, label, time_, 'security', ekspedisi[0])
                print(last_loc)
                print(ekspedisi)
                if last_loc == 'masuk':
                    message = 'Kendaraan: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                else:
                    message = 'Kendaraan: {} Berhasil Masuk.'.format(label)
                    message_type = 'success'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label, type=ekspedisi)
            
            else:
                last_loc = masuk_223(date_, label, time_, 'security', '-')
                if last_loc == 'masuk':
                    message = 'Kendaraan: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                else:
                    message = 'Kendaraan: {} Berhasil Masuk.'.format(label)
                    message_type = 'success'
                    return redirect(url_for('unknown', message=message, message_type=message_type, data=data, label=label))
            
            # return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
            
    return render_template('ocr.html')

@app.route('/ocr/unknown', methods=['GET', 'POST'])
def unknown():
    message = request.args.get('message')
    message_type = request.args.get('message_type')
    data = request.args.get('data')
    label = request.args.get('label')
    if request.method == 'POST':
        pass
    
    return render_template('unknown.html', message=message, message_type=message_type, data=data, label=label)

@app.route('/ocr/ga/input_km', methods=['GET', 'POST'])
def input_km():
    if request.method == 'POST':
        km = request.form.get('km')
        action = request.form.get('action')
        no_mobil = request.form.get('no_mobil')
        print(km)
        print(action)
        print(no_mobil)
        return redirect(url_for('ocr'))
    
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5001,
    )