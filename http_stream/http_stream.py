import argparse

import cv2
import imagezmq
from werkzeug import Request, Response, run_simple

receiver_ip = None

def send_images_to_web():
    receiver = imagezmq.ImageHub(open_port=receiver_ip, REQ_REP= False)
    while True:
        sender_name, image = receiver.recv_image()
        jpg = cv2.imencode('.jpg', image)[1]
        yield b'--frame\r\nContent-Type:image/jpeg\r\n\r\n'+jpg.tostring()+b'\r\n'


@Request.application
def application(request):
    return Response(send_images_to_web(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="This is HTTP stream monitor which will receive "
                    "real time video from receiver and show the result "
                    "on browser")

    parser.add_argument('--receiver_ip', required=False,
                        help='Please provide the receiver IP, '
                             'example: python3 http_stream.py --receiver_ip '
                             '\'tcp://192.168.0.101:5566\', '
                             'default = \'tcp://0.0.0.0:5566\'',
                        type=str,
                        default='tcp://0.0.0.0:5566'
                        )

    args = parser.parse_args()

    receiver_ip = args.receiver_ip

    run_simple('192.168.0.101', 4000, application)
