# import threading
# import requests
# import queue

# def make_request(mt_q):
#     while True:
#         url = mt_q.get()
#         try:
#             response = requests.get(url)
#             if response.status_code == 200:
#                 print(f'Successfully retrieved data from {url}')
#             else:
#                 print(f'Response error from {url}: {response.status_code}')
#         except requests.exceptions.RequestException as e:
#             print(f'An error occurred while retrieving data from {url}: {e}')
#         mt_q.task_done()

# urls = ['http://localhost/FL/mt.php?', 'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         'http://localhost/FL/mt.php?',
#         ]

# mt_q = queue.Queue()

# # Create worker threads
# for i in range(2):
#     t = threading.Thread(target=make_request, args=(mt_q,), daemon=True)
#     t.start()

# # Add data to the queue
# for url in urls:
#     mt_q.put(url)

# # Wait for the queue to be empty
# mt_q.join()

# ss = "_".join(["tes1","tes2"])
# # result = "test1_tes2"
# print(ss)

import threading
import time

def thread(stop):
    while True:
        print("RUNNING")
        if exitflag1:
            break
exitflag1 = False
t1 = threading.Thread(target = thread, args =(lambda : exitflag1, ))
t1.start()
time.sleep(0.1)
print('Stop the threads.')
exitflag1 =True
t1.join()
print('TERMINATED!')
