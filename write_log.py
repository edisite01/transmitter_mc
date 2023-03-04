import logging
import datetime
import configparser
import os


def write_log(thread = "No Thread", tinfo = "Info",  message ="-"):
    # mendapatkan tanggal saat ini
    today = datetime.date.today()
    config = configparser.ConfigParser()
    config.read('config.cfg')

    log_file = config.get('log', 'file')
    log_dir = config.get('log', 'directory')
    log_filename = f"{log_file}_{today.strftime('%Y-%m-%d')}.log"

    log_file_path = os.path.join(log_dir, log_filename)

    # membuka file log
    with open(log_file_path, 'a') as f:
        # membuat timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # menuliskan pesan log ke dalam file
        f.write(f'{timestamp} - {thread} - {tinfo} - {message}\n')
