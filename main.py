# import socket
import signal
import requests
from xml.etree import ElementTree as ET
import threading
import time
# from connect_to_database import connect_to_database
from configparser import ConfigParser
import os
import sys
# sys.path.append('src/')
# dir_path = os.path.dirname(os.path.abspath(__file__))
# src_dir = os.path.join(dir_path, 'src')
# sys.path[0] =src_dir
from mariapy import MariaDBHelper as db

# from write_log import write_log
import urllib.parse

import datetime

import queue

# daabase connection
conn = db()

path_current_directory = os.path.dirname(__file__)
path_config_file = os.path.join(path_current_directory, '', 'config.cfg')
config = ConfigParser()
config.read(path_config_file)
api_url = config.get('api', 'url')

maxworker = config.get('threads', 'maxworker')
log_file = config.get('log', 'file')
log_dir = config.get('log', 'directory')

mt_q = queue.Queue(maxsize=200)
gqueEXEC = queue.Queue(400)

def write_log(tinfo = "Info",  message ="-", trxid= ""):
    # mendapatkan tanggal saat ini
    today = datetime.date.today()

    log_filename = f"{log_file}_{today.strftime('%Y-%m-%d')}.log"

    log_file_path = os.path.join(log_dir, log_filename)

    # membuka file log
    with open(log_file_path, 'a') as f:
        # membuat timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        threadname =threading.current_thread().getName()
        # menuliskan pesan log ke dalam file
        f.write(f'{timestamp}|{threadname:<8}|{trxid:<8}|{tinfo:<15} | {message}\n')


# Fungsi untuk mengirimkan data ke API
# def send_data(tmtdc_id,trx_id,sid,msisdn,sms,smstype,delivery_method,shortcode,keyword,isms,subtype,age,mediacode,objectId,waptype):
def send_data(q_in):
    while True:
        try:
            # write_log("info"," q_in tget ")
            tget = q_in.get_nowait()
        except queue.Empty:
            # write_log("error"," Failed Queue Empty")
            # process()
            continue

        trx_id = tget['trx_id']
        tmtdc_id = tget['tmtdc_id']
        msisdn = tget['msisdn']
        sms = tget['sms']
        write_log("Begin ", " ",trx_id)

        if trx_id =="" or tmtdc_id == "" or msisdn == "" or sms == "":
            write_log("error"," Parameter Incomplete : "+ str(tget),trx_id)
            conn.connect()
            conn.resetQuery()
            conn.Update('t_mt_dc')
            conn.Set(['sts'])
            conn.Where('tmtdc_id = ' + str(tmtdc_id))
            conn.execute(("9",))
            write_log("error"," update tmtdc : "+ conn.getQuery(),trx_id)
            conn.commit()
            conn.disconnect()
            pass
        parameter = {}
        parameter = {
            'transid':tget['trx_id'],
            'serviceid':tget['sid'],
            'msisdn':tget['msisdn'],
            'sms':tget['sms'],
            'smstype':tget['smstype'],
            'delivery_method':tget['delivery_method'],
            'shortcode':tget['shortcode'],
            'keyword':tget['keyword'],
            'isms':tget['isms'],
            'subtype':tget['subtype'],
            'age':tget['age'],
            'mediacode':tget['mediacode'],
            'objectId':tget['objectId'],
            'waptype':tget['waptype'],
        }
        write_log("Send Data", api_url + urllib.parse.urlencode(parameter),trx_id)
        # # mengirim data ke server

        try:
            response = requests.get(api_url, params=parameter)
        except requests.exceptions.RequestException as e:
            write_log("error", f'An error occurred while retrieving data from {api_url}: {e}',trx_id)
            t_update = """UPDATE t_mt_dc SET sts = 3 WHERE tmtdc_id = %s""" % tmtdc_id
            gqueEXEC.put({'ttrxid':trx_id,'tmsg':'counted as error','tsql':t_update})
            write_log("error update sql", t_update,trx_id)
            pass

        # Parsing respon
        response_status_code = response.status_code
        response_text = response.text
        if response_status_code == 200:
            rtext = ET.fromstring(response_text)
            xml_str = ET.tostring(rtext, encoding='unicode', method='xml')
            write_log("Response", xml_str,trx_id)
            status = rtext.find('status').text

            if status == "0":
                t_update = """UPDATE t_mt_dc SET sts = 1 WHERE tmtdc_id = %s""" % tmtdc_id
                gqueEXEC.put({'ttrxid':trx_id,'tmsg':'counted as sucess','tsql':t_update})
            else:
                t_update = """UPDATE t_mt_dc SET sts = 3 WHERE tmtdc_id = %s""" % tmtdc_id
                gqueEXEC.put({'ttrxid':trx_id,'tmsg':'counted as error','tsql':t_update})
                write_log("error update sql", t_update,trx_id)
        else:
            write_log("info"," Response Failed (HTTP)" + str(response_status_code) + str(response_text),trx_id)
            # slee 3 second
            t_update = """UPDATE t_mt_dc SET sts = 3 WHERE tmtdc_id = %s""" % tmtdc_id
            gqueEXEC.put({'ttrxid':trx_id,'tmsg':'counted as error','tsql':t_update})
            write_log("error update sql", t_update,trx_id)
            time.sleep(1)
        q_in.task_done()
        # time.sleep(1)

# Fungsi untuk membaca data dari database dan mengirimkannya ke API
def process():
    while True:
        # print("thread count0",threading.active_count())
        if mt_q.full() or gqueEXEC.full():
            write_log("info"," Queue isfull -> sleep 3 second ")
            write_log("Size of Queue", "mt_q :" +str(mt_q.qsize()))
            write_log("Size of Queue", "gqueEXEC : "+str(gqueEXEC.qsize()))
            write_log("info"," \n\n")
            time.sleep(3)
            process()
            return

        # write_log("mt_q - Size of Queue", str(mt_q.qsize()))
        # write_log("gqueEXEC - Size of Queue", str(gqueEXEC.qsize()))
        rows= ""
        conn.connect()
        conn.resetQuery()
        conn.SelectAll()
        conn.From('t_mt_dc')
        conn.Where('sts=0 ORDER BY `t_mt_dc`.`method` ASC limit 100')
        conn.execute()
        conn.cursor._dictionary = True
        rows = conn.getCursor().fetchall()

        # Jika tidak ada data yang ditemukan, tidur selama 10 detik dan coba lagi
        if not rows:
            write_log("info"," Queue empty -> sleep 3 second ")
            time.sleep(3)
            process()
            return
        # for row in rows:
        tmtdcids = [(row[0]) for row in rows]
        t_update = "UPDATE t_mt_dc SET sts = 2 WHERE tmtdc_id IN ({})".format(','.join(str(x) for x in tmtdcids))

        # conn.connect()
        conn.resetQuery()
        conn.AddCustomQuery(t_update)
        conn.execute()
        conn.commit()

        for row in rows:
            parameter = {
                'tmtdc_id':row[0],
                'trx_id':row[7],
                'sid':row[2],
                'msisdn':row[3],
                'sms':row[9],
                'smstype':row[11],
                'delivery_method':row[10],
                'shortcode':row[12],
                'keyword':row[13],
                'isms':row[14],
                'subtype':0,
                'age':row[15],
                'mediacode':row[19],
                'objectId':row[17],
                'waptype':row[21],
            }
            try:
                mt_q.put_nowait(parameter)
            except queue.FULL:
                write_log("info","mtq_q putis queue.full :" + parameter)
                break

        conn.disconnect()
        mt_q.join()
        gqueEXEC.join()
        time.sleep(1)


def proces_respons(qexec):
    while True:
        try:
            gqeGet = qexec.get()
        except queue.Empty:
            return
        trx_id = gqeGet['ttrxid']
        tmsg = gqeGet['tmsg']
        tsql = gqeGet['tsql']

        write_log("execute",str(tsql),trx_id)
        conn.connect()
        conn.resetQuery()
        conn.AddCustomQuery(tsql)
        conn.execute()
        conn.commit()
        conn.disconnect()
        write_log("msg",tmsg,trx_id)
        write_log("End"," \n",trx_id)
        qexec.task_done()

# Fungsi utama
def main():
    write_log("setting","api url : " + api_url)
    write_log("setting","thread : " + maxworker)
    write_log("setting","log file name : " + log_file)
    write_log("setting","log directory : " + log_dir)

    threads = []
    for i in range(int(maxworker)):
        t_threadName =  "_".join(["thread_t", str(i)])
        t = threading.Thread(target=send_data, args=(mt_q,), name=t_threadName)
        t.daemon = True
        threads.append(t)
        t.start()

    for i in range(1):
        t_threadName =  "_".join(["thread_r", str(i)])
        t = threading.Thread(target=proces_respons, args=(gqueEXEC,), name=t_threadName)
        t.daemon = True
        threads.append(t)
        t.start()




    # print("thread count1",threading.active_count())
    write_log("setting","Running Thread : " + str(threading.active_count()))
    process()


if __name__ == '__main__':
    write_log("Info ","Application started ------------------")
    main()
