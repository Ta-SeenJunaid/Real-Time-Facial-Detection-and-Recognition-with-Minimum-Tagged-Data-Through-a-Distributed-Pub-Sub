import argparse
import os
import sys
import threading
import traceback

import cv2
import imagezmq

from image_processing import find_encodings, process_image


def bootstrap_args_type_sender_ips(sender_ips_str_arg):
    sender_ip = []
    for arg in sender_ips_str_arg.split(','):
        arg = str(arg)
        sender_ip.append(arg)

    return sender_ip


class Receiver:

    def __init__(self, tcp_ip, stream_monitor_tcp_ip=None):
        self.tcp_ip = tcp_ip
        self.image_hub = imagezmq.ImageHub(self.tcp_ip, REQ_REP=False)
        if stream_monitor_tcp_ip:
            self.stream_monitor = imagezmq.ImageSender(
                connect_to=stream_monitor_tcp_ip,
                REQ_REP=False)
        self._stop = False
        self._data_ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def receive(self, timeout=1000.00):
        flag = self._data_ready.wait(timeout=timeout)
        if not flag:
            raise TimeoutError(
                f'Timeout while reading from subscriber {self.tcp_ip}'
            )
        self._data_ready.clear()
        return self._data

    def _run(self):
        while not self._stop:
            self._data = self.image_hub.recv_image()
            self._data_ready.set()
        self.image_hub.close()

    def close(self):
        self._stop = True


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="This is receiver which will receive"
                    "real time video from sender")

    parser.add_argument('--sender_ip', required=False,
                        help='please provide all the sender IP in comma separated formation, '
                             'example: python3 receiver.py --sender_ip \'tcp://192.168.0.101:5555, '
                             'tcp://192.168.0.106 :5555\', '
                             'default= tcp://0.0.0.0:5555 ',
                        type=bootstrap_args_type_sender_ips,
                        default='tcp://0.0.0.0:5555')

    parser.add_argument('--stream_monitor_ip', required=False,
                        help='please provide the stream monitor IP, '
                             'example: python3 receiver.py --stream_monitor_ip \'tcp://192.168.0.101:5566\', '
                             'default=None',
                        type=str,
                        default=None)

    args = parser.parse_args()

    path = 'image_attendance'
    images = []
    class_names = []
    my_list = os.listdir(path)

    for cl in my_list:
        cur_img = cv2.imread(f'{path}/{cl}')
        images.append(cur_img)
        class_names.append(os.path.splitext(cl)[0])
    print(class_names)

    encode_list_known = find_encodings(images)
    print('Encoding Complete')

    if args.stream_monitor_ip:
        receiver = Receiver(args.sender_ip[0], args.stream_monitor_ip)
    else:
        receiver = Receiver(args.sender_ip[0])

    for sender_tcp_ip in args.sender_ip[1:]:
        receiver.image_hub.connect(sender_tcp_ip)

    try:
        while True:
            sender_name, image = receiver.receive()
            if args.stream_monitor_ip:
                sender_name, image = process_image(
                        image, sender_name, encode_list_known,
                        class_names, args.stream_monitor_ip)
                receiver.stream_monitor.send_image(sender_name, image)
            else:
                process_image(image, sender_name, encode_list_known, class_names)
    except (KeyboardInterrupt, SystemExit):
        print('Exit due to keyboard interrupt')
    except Exception as ex:
        print('Python error with no Exception handler:')
        print('Traceback error:', ex)
        traceback.print_exc()
    finally:
        receiver.close()
        sys.exit()
