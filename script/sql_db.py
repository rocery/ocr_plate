import mysql.connector
import re

def db_connection(host, user, password, database):
    """Connect to MySQL database.

    :param host: hostname or ip address of mysql server
    :param user: username to use for connection
    :param password: password to use for connection
    :param database: database name to use
    :return: a database connection
    """
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

def iot_223():
    return db_connection('192.168.15.223', 'admin', 'itbekasioke', 'iot')

def parkir_220():
    return db_connection('192.168.15.220', 'user_external_220', 'Sttbekasioke123!', 'parkir')

def db_pegawai_220():
    return db_connection('192.168.15.220', 'user_external_220', 'Sttbekasioke123!', 'db_pegawai')

def normalize_no_mobil(no_mobil):
    return re.sub(r'\s+', '', no_mobil).upper()

def get_ekspedisi(no_mobil):
    no_mobil_normalized = normalize_no_mobil(no_mobil)
    
    conn_parkir = parkir_220()
    cursor_parkir = conn_parkir.cursor()
    
    cursor_parkir.execute("""
        SELECT nama_ekspedisi, panjang, lebar, tinggi, cbm, jn_kendaraan FROM pengukuran
        WHERE REPLACE(REPLACE(nomor_polisi, ' ', ''), '-', '') = %s
    """, (no_mobil_normalized,))
    result = cursor_parkir.fetchone()
    
    cursor_parkir.close()
    conn_parkir.close()
    
    return result if result else None

def get_kendaraan_ga(no_mobil):
    no_mobil_normalized = normalize_no_mobil(no_mobil)
    
    conn_db_pegawai = db_pegawai_220()
    cursor_db_pegawai = conn_db_pegawai.cursor()
    
    cursor_db_pegawai.execute("""
        SELECT jenis_kendaraan FROM kendaraan
        WHERE REPLACE(REPLACE(nopol, ' ', ''), '-', '') = %s
    """, (no_mobil_normalized,))
    result = cursor_db_pegawai.fetchone()
    
    cursor_db_pegawai.close()
    conn_db_pegawai.close()
    
    return True if result else False

def masuk_223(tanggal, no_mobil, jam_masuk_pabrik, user_in, ekspedisi):
    conn_masuk_223 = iot_223()
    cursor_masuk_223 = conn_masuk_223.cursor()
    
    # Cek Status Terakhir
    cursor_masuk_223.execute("""
        SELECT * FROM ocr
        WHERE no_mobil = %s AND (tanggal_keluar IS NULL OR jam_keluar IS NULL)
    """, (no_mobil,))
    check_last_status = cursor_masuk_223.fetchone()
    
    if check_last_status:
        return 'masuk'
    
    cursor_masuk_223.execute("""
        INSERT INTO ocr (tanggal, no_mobil, jam_masuk_pabrik, user_in, ekspedisi)
        VALUES (%s, %s, %s, %s, %s)
    """, (tanggal, no_mobil, jam_masuk_pabrik, user_in, ekspedisi))
    conn_masuk_223.commit()
    
    cursor_masuk_223.close()
    conn_masuk_223.close()
    
def keluar_223(tanggal, no_mobil, jam_keluar_pabrik, user_out):
    conn_keluar_223 = iot_223()
    cursor_keluar_223 = conn_keluar_223.cursor()
    no_mobil_normalized = normalize_no_mobil(no_mobil)
    
    # Cek Status Terakhir
    cursor_keluar_223.execute("""
        SELECT * FROM ocr
        WHERE no_mobil = %s AND tanggal_keluar IS NULL AND jam_masuk_pabrik IS NOT NULL
    """, (no_mobil_normalized,))
    result = cursor_keluar_223.fetchone()
    
    if not result:
        return 'keluar'
    
    cursor_keluar_223.execute("""
        UPDATE ocr
        SET tanggal_keluar = %s, jam_keluar = %s, user_out = %s
        WHERE no_mobil = %s AND tanggal_keluar IS NULL
    """, (tanggal, jam_keluar_pabrik, user_out, no_mobil_normalized))
    conn_keluar_223.commit()
    
    cursor_keluar_223.close()
    conn_keluar_223.close()
    
def ga_km_process(no_mobil, km, action):
    conn_ga_km_process = iot_223()
    cursor_ga_km_process = conn_ga_km_process.cursor()
    no_mobil_normalized = normalize_no_mobil(no_mobil)
    
    try:
        # Step 1: Get the latest tanggal for the given no_mobil
        cursor_ga_km_process.execute("""
            SELECT MAX(tanggal) 
            FROM ocr 
            WHERE no_mobil = %s
        """, (no_mobil_normalized,))
        latest_date = cursor_ga_km_process.fetchone()[0]
        if latest_date is None:
            return False
        
        # Step 2: Get the latest time for the given no_mobil
        cursor_ga_km_process.execute("""
            SELECT MAX(jam_masuk_pabrik) 
            FROM ocr 
            WHERE no_mobil = %s
            AND tanggal = %s
        """, (no_mobil_normalized, latest_date))
        latest_time = cursor_ga_km_process.fetchone()[0]
        if latest_time is None:
            return False
        
        if action == 'Masuk':
            print("Proses km_in")
            cursor_ga_km_process.execute("""
                UPDATE ocr
                SET km_in = %s
                WHERE no_mobil = %s 
                AND ekspedisi = 'GA'
                AND tanggal = %s
                AND jam_masuk_pabrik = %s
            """, (km, no_mobil_normalized, latest_date, latest_time))
            conn_ga_km_process.commit()

        elif action == 'Keluar':
            print("Proses km_out")
            cursor_ga_km_process.execute("""
                UPDATE ocr
                SET km_out = %s
                WHERE no_mobil = %s 
                AND ekspedisi = 'GA'
                AND tanggal = %s
                AND jam_masuk_pabrik = %s
            """, (km, no_mobil_normalized, latest_date, latest_time))
            conn_ga_km_process.commit()

    except Exception as e:
        print(f"An error occurred: {e}")
        conn_ga_km_process.rollback()  # Rollback in case of error
        
    cursor_ga_km_process.close()
    conn_ga_km_process.close()
    
def masuk_223_tamu(no_mobil, jenis_tamu):
    conn_masuk_223_tamu = iot_223()
    cursor_masuk_223_tamu = conn_masuk_223_tamu.cursor()
    no_mobil_normalized = normalize_no_mobil(no_mobil)
    
    # Step 1: Get the latest tanggal for the given no_mobil
    cursor_masuk_223_tamu.execute("""
        SELECT MAX(tanggal) 
        FROM ocr 
        WHERE no_mobil = %s
    """, (no_mobil_normalized,))
    latest_date = cursor_masuk_223_tamu.fetchone()[0]
    if latest_date is None:
        return False
    
    # Step 2: Get the latest time for the given no_mobil
    cursor_masuk_223_tamu.execute("""
        SELECT MAX(jam_masuk_pabrik) 
        FROM ocr 
        WHERE no_mobil = %s
        AND tanggal = %s
    """, (no_mobil_normalized, latest_date))
    latest_time = cursor_masuk_223_tamu.fetchone()[0]
    if latest_time is None:
        return False
    
    if jenis_tamu == 'Ekspedisi':
        cursor_masuk_223_tamu.execute("""
            UPDATE ocr
            SET ekspedisi = %s
            WHERE no_mobil = %s
            AND tanggal = %s
            AND jam_masuk_pabrik = %s
        """, (jenis_tamu, no_mobil_normalized, latest_date, latest_time))
        conn_masuk_223_tamu.commit()

    elif jenis_tamu == 'Tamu':
        cursor_masuk_223_tamu.execute("""
            UPDATE ocr
            SET ekspedisi = %s
            WHERE no_mobil = %s
            AND tanggal = %s
            AND jam_masuk_pabrik = %s
        """, (jenis_tamu, no_mobil_normalized, latest_date, latest_time))
        conn_masuk_223_tamu.commit()
    
    cursor_masuk_223_tamu.close()
    conn_masuk_223_tamu.close()
    return True

def list_tamu():
    # SELECT * FROM `ocr` WHERE ekspedisi = 'Tamu' AND pic_stt IS NULL AND keperluan IS NULL ORDER BY tanggal DESC, jam_masuk_pabrik DESC;
    
    conn_edit_tamu = iot_223()
    cursor_edit_tamu = conn_edit_tamu.cursor()
    cursor_edit_tamu.execute("""
        SELECT 
            CONCAT(tanggal, ' ', jam_masuk_pabrik) AS waktu_masuk,
            no_mobil,
            ekspedisi,
            pic_stt,
            keperluan,
            CONCAT(tanggal_keluar, ' ', jam_keluar) AS waktu_keluar
        FROM 
            ocr
        WHERE ekspedisi = 'Tamu'
        -- AND pic_stt IS NULL
        -- AND keperluan IS NULL
        ORDER BY tanggal DESC, jam_masuk_pabrik DESC
    """)
    result = cursor_edit_tamu.fetchall()
    
    cursor_edit_tamu.close()
    conn_edit_tamu.close()
    return result

def edit_tamu_sql(datetime, no_mobil, keperluan, pic_stt):
    conn_edit_tamu = iot_223()
    cursor_edit_tamu = conn_edit_tamu.cursor()
    cursor_edit_tamu.execute("""
        UPDATE ocr
        SET pic_stt = %s, keperluan = %s
        WHERE no_mobil = %s
        AND ekspedisi = 'Tamu'
        AND CONCAT(tanggal, ' ', jam_masuk_pabrik) = %s
    """, (pic_stt, keperluan, no_mobil, datetime))
    conn_edit_tamu.commit()
    
    cursor_edit_tamu.close()
    conn_edit_tamu.close()