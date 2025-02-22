from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
import time
from script.ocr_process import ocr_predict, img_preprocess, show_labels, numpy_to_base64, save_image_ocr
from script.licence_plate_detector import detect_license_plate
from script.char_prosess import character_check
from script.sql_db import *
from script.csv_process import read_data_csv
from script.fast_alpr_script import fast_alpr_process
import re
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'itbekasioke'
USER_SECRET_KEY = 'user123'
USER_EDIT_TAMU_KEY = 'tamu123'

@app.route('/ocr/login_ocr', methods=['GET', 'POST'])
def login_ocr():
    if request.method == 'POST':
        secret_key = request.form.get('secret_key')
        if secret_key == USER_SECRET_KEY:
            session['authenticated'] = True
            return redirect(url_for('ocr'))
        elif secret_key == USER_EDIT_TAMU_KEY:
            session['authenticated'] = True
            return redirect(url_for('edit_tamu'))
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
        action = request.form['action']
        image = request.files['image']
        
        try:
            entryType = request.form['entryType']
        except:
            return render_template('ocr.html', message='Jenis Kendaraan Tidak Valid. Mohon Untuk Input Ulang.', message_type='danger')
        km = None
        
        if entryType == 'GA':
            km = request.form.get('km')
            print(type(km))
            if km == '' or km is None:
                return render_template('ocr.html', message='KM GA Tidak Valid. Mohon Untuk Input Ulang.', message_type='danger')
        
        print(f"Action: {action}, Img: {type(image)}, Entry Type: {entryType}, KM: {km}")
        
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
                    # Save to csv undetected_plate.csv
                    message = 'Tidak Terdeteksi Plat Nomor Pada Gambar. Silahkan Ulangi Proses Upload. Error Code: 0x1'
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type)
                
                ocr_result = ocr_predict(image)
                
                if ocr_result == False:
                    # Save to csv undetected_ocr.csv
                    message = 'Tidak Terdeteksi Angka/Huruf Pada Foto. Silahkan Ulangi Proses Upload. Error Code: 0x2'
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type)
                
                show_label = show_labels(image, ocr_result)
                label = show_label[1]
                data = numpy_to_base64(show_label[0])
                
                result, value = character_check(label)
                if result == False:
                    # Save to csv wrong_ocr.csv
                    message = 'Plat Nomor Terbaca Salah. Mohon Ulangion Proses Upload. Error Code: 0x3'
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                else:
                    label = value
                    
                ## def save_image_ocr(image, file_name, folder_date, time_input, label, action):
                # save_image_ocr(show_label[0], file_name, date_str, time_str, label, action)
                # Save Image (img, date, datetime, nomobil, action)
                # "label_action_date_time.file_extension"
                save_image_ocr(show_label[0], time_str, label, action)
                
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
            last_loc = None
            if entryType == 'Ekspedisi':
                ekspedisi = get_ekspedisi(label)
                if ekspedisi is not None:
                    last_loc = masuk_223(date_, label, time_, 'security', ekspedisi[0])
                    if last_loc == 'masuk':
                        message = 'Ekspedisi: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
                        message_type = 'danger'
                        return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                    else:
                        message = 'Ekspedisi: {} Berhasil Masuk.'.format(label)
                        message_type = 'success'
                        return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label, type=ekspedisi)
                else:
                    masuk_223(date_, label, time_, 'security', entryType)
                    message = 'Ekspedisi: {} Tidak Terdaftar. Proses Tetap Dilanjutkan.'.format(label)
                    message_type = 'warning'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
            
            elif entryType == 'GA':
                status_kendaraan_ga = get_kendaraan_ga(label)
                if status_kendaraan_ga:
                    last_loc = masuk_223(date_, label, time_, 'security', entryType, km)
                    if last_loc == 'masuk':
                        message = 'GA: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
                        message_type = 'danger'
                        return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                    else:
                        message = 'GA: {} Berhasil Masuk.'.format(label)
                        message_type = 'success'
                        return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                else:
                    message = 'GA: {} Tidak Terdaftar Sebagai GA.'.format(label)
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                
            elif entryType == 'Tamu':
                last_loc = masuk_223(date_, label, time_, 'security', entryType)
                if last_loc == 'masuk':
                    message = 'Tamu: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
                    message_type = 'danger'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                else:
                    message = 'Tamu: {} Berhasil Masuk. Hubungi Admin Untuk Pengisian Data PIC dan Keperluan.'.format(label)
                    message_type = 'success'
                    return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
                
            else:
                message = 'Keperluan Tidak Diketahui.'
                message_type = 'danger'
                return render_template('ocr.html', message=message, message_type=message_type)
            
        if action == 'Keluar':
            last_loc = keluar_223(date_, label, time_, 'security', km)
            if last_loc == 'keluar':
                message = 'Kendaraan: {} Sudah Didalam. Tidak Bisa Diproses Keluar 2x.'.format(label)
                message_type = 'danger'
                return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
            else:
                message = 'Kendaraan: {} Berhasil Keluar.'.format(label)
                message_type = 'success'
                return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
            
        # if action == 'Masuk':
        #     # print("Plat Nomor : {}".format(label))
        #     # print("Data Gambar: {}".format(type(data)))
        #     last_loc = None
            
        #     if status_kendaraan_ga == True:
        #         last_loc = masuk_223(date_, label, time_, 'security', 'GA')
        #         print(last_loc)
        #         print(status_kendaraan_ga)
        #         if last_loc == 'masuk':
        #             message = 'Kendaraan: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
        #             message_type = 'danger'
        #             return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
        #         else:
        #             message = 'Kendaraan: {} Berhasil Masuk.'.format(label)
        #             message_type = 'success'
        #             return render_template('ocr.html',
        #                                    message=message,
        #                                    message_type=message_type,
        #                                    data=data,
        #                                    label=label,
        #                                    type='GA',
        #                                    action=action)
            
        #     elif ekspedisi:
        #         last_loc = masuk_223(date_, label, time_, 'security', ekspedisi[0])
        #         print(last_loc)
        #         print(ekspedisi)
        #         if last_loc == 'masuk':
        #             message = 'Kendaraan: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
        #             message_type = 'danger'
        #             return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
        #         else:
        #             message = 'Kendaraan: {} Berhasil Masuk.'.format(label)
        #             message_type = 'success'
        #             return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label, type=ekspedisi)
            
        #     else:
        #         last_loc = masuk_223(date_, label, time_, 'security', '-')
        #         if last_loc == 'masuk':
        #             message = 'Kendaraan: {} Sudah Didalam. Tidak Bisa Diproses Masuk 2x.'.format(label)
        #             message_type = 'danger'
        #             return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
        #         else:
        #             message = 'Kendaraan: {} Berhasil Masuk.\nPlat Nomor Tidak Terdaftar.'.format(label)
        #             message_type = 'warning'
        #             return render_template('unknown.html', message=message, message_type=message_type, data=data, label=label)
            
        #     # return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
        
        # elif action == 'Keluar':
        #     last_loc = None
            
        #     last_loc = keluar_223(date_, label, time_, 'security')
            
        #     if last_loc == 'keluar':
        #         message = 'Kendaraan: {} Sudah Di Keluar. Tidak Bisa Diproses Keluar 2x.'.format(label)
        #         message_type = 'danger'
        #         return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
            
        #     else:
        #         message = 'Kendaraan: {} Berhasil Keluar.'.format(label)
        #         message_type = 'success'
        #         if status_kendaraan_ga == True:
        #             return render_template('ocr.html',
        #                                 message=message,
        #                                 message_type=message_type,
        #                                 data=data,
        #                                 label=label,
        #                                 type='GA',
        #                                 action=action)
                
        #         else:
        #             return render_template('ocr.html', message=message, message_type=message_type, data=data, label=label)
    
    return render_template('ocr.html')

@app.route('/ocr/unknown', methods=['GET', 'POST'])
def unknown():
    if request.method == 'GET':
        try:
            message = request.args.get('message')
            message_type = request.args.get('message_type')
            data = request.args.get('data')
            label = request.args.get('label')
            return render_template('unknown.html', message=message, message_type=message_type, data=data, label=label)
        except:
            print("Error GET Data unknown()")
            message = 'Error GET Data unknown() pada Proses Tamu.'
            message_type = 'danger'
            return render_template('ocr.html', message=message, message_type=message_type)
    
    if request.method == 'POST':
        try:
            keperluan = request.form.get('inputTujuanList')
            no_mobil = request.form.get('no_mobil')
            
            if keperluan == 'Lainnya/Tamu':
                keperluan = 'Tamu'
                
            print(f"{keperluan}, {no_mobil}")
            
            if keperluan == 'Ekspedisi' or keperluan == 'Tamu':
                masuk = masuk_223_tamu(no_mobil, keperluan)
            
            if masuk:
                message = 'Kendaraan: {} Berhasil Masuk. Tujuan: {}'.format(no_mobil, keperluan)
                message_type = 'success'
                return render_template('ocr.html', message=message, message_type=message_type)
            else:
                message = 'Kendaraan: {} Tidak Ditemukan. Tujuan: {}'.format(no_mobil, keperluan)
                message_type = 'danger'
                return render_template('ocr.html', message=message, message_type=message_type)
        
        except:
            message = 'Error POST Data unknown() pada Proses Tamu.'
            message_type = 'danger'
            return render_template('ocr.html', message=message, message_type=message_type)
    
    return redirect(url_for('ocr'))

@app.route('/ocr/ga/input_km', methods=['GET', 'POST'])
def input_km():
    if request.method == 'POST':
        km = request.form.get('km')
        action = request.form.get('action')
        no_mobil = request.form.get('no_mobil')
        
        print(f"Data Input KM: {no_mobil} {km} {action}")
        
        status = ga_km_process(no_mobil, km, action)
        if status == False:
            message = 'Data Kendaraan: {} Tidak Ditemukan.'.format(no_mobil)
            message_type = 'danger'
            return render_template('ocr.html', message=message, message_type=message_type)
        
        else:
            message = 'Kendaraan GA: {} Berhasil {}. KM: {}.'.format(no_mobil, action, km)
            message_type = 'success'
            return render_template('ocr.html', message=message, message_type=message_type)
        
    return redirect(url_for('ocr'))

@app.route("/ocr/get_data_all_ocr")
def get_data_all_ocr():
    data = read_data_csv()
    return jsonify(data)

STRING_REGEX = re.compile(r"^[A-Za-z\s]+$")
@app.route("/ocr/edit_tamu", methods=['GET', 'POST'])
def edit_tamu():
    if not session.get('authenticated'):
        return redirect(url_for('login_ocr'))
    
    list_keperluan = ['Interview', 'BS', 'Sampah', 'Tamu', 'Sales', 'Lainnya']
    data = list_tamu()
    
    if request.method == 'POST':
        try:
            no_mobil = request.form['noMobil']
            pic_stt = request.form['picSTT']
            keperluan = request.form['keperluan']
            datetime = request.form['dateTime']
        except:
            print("Data tidak ada")
            
        print(f"{no_mobil}, {pic_stt}, {keperluan}, {datetime}")
            
        if not STRING_REGEX.match(pic_stt):
            flash('Input PIC STT harus berupa huruf.', 'danger')
            return redirect(url_for('edit_tamu'))
            
        status_edit = edit_tamu_sql(datetime, no_mobil, keperluan, pic_stt)
        if status_edit != False:
            flash(f'Data Tamu {no_mobil} Berhasil Diperbarui.', 'success')
            return redirect(url_for('edit_tamu'))
    
    return render_template('edit_tamu.html', list_tamu=data, list_keperluan=list_keperluan)

@app.route("/ocr/list_ga")
def list_ga():
    data = list_ga_sql()
    return render_template('list_ga.html', data = data)

@app.route("/ocr/list_ekspedisi")
def list_ekspedisi():
    data = list_ekspedisi_sql()
    return render_template('list_ekspedisi.html', data = data)

@app.route("/ocr/data_ocr")
def data_ocr():
    data = all_data_sql()
    return render_template('data_ocr.html', data = data)

@app.route('/ocr/try', methods=['GET', 'POST'])
def try_():
    if request.method == 'POST':
        action = request.form['action']
        image = request.files['image']
        
        try:
            entryType = request.form['entryType']
        except:
            return render_template('try.html', message='Jenis Kendaraan Tidak Valid. Mohon Untuk Input Ulang.', message_type='danger')    

        km = None
        
        if entryType == 'GA':
            km = request.form.get('km')
            if km == '' or km is None:
                return render_template('try.html', message='KM Kendaraan GA Tidak Valid. Mohon Untuk Input Ulang.', message_type='danger')

        print(f"Action: {action}, Img: {type(image)}, Entry Type: {entryType}, KM: {km}")
        
        if image:
            try:
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                time_ = time.strftime("%H:%M:%S", time.localtime())
                date_ = time.strftime("%Y-%m-%d", time.localtime())
                
                image = img_preprocess(image, action, time_str)
                print(type(image))
                
                fast_alpr = fast_alpr_process(image)
                return render_template('try.html', message=fast_alpr, message_type='success')
            
            except:
                return render_template('try.html', message='Gagal Memproses Gambar. Mohon Untuk Input Ulang.', message_type='danger')
                
    return render_template('try.html')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
