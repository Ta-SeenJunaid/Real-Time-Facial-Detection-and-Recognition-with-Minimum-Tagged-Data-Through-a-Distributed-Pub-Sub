import socket
import sys
import time
import traceback

from imutils.video import VideoStream
import imagezmq
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="This is sender which will send"
                    "real time video to receiver")

    parser.add_argument('--sender_ip', required=False,
                        help='please provide the sender IP, '
                             'example: --sender_ip \'tcp://192.168.0.101:5555\', '
                             'default=\'tcp://0.0.0.0:5555\'',
                        type=str,
                        default='tcp://0.0.0.0:5555')

    parser.add_argument('--host_camera_type', required=False,
                        help='please provide the host camera type, '
                             '\'Pi Camera\' or \'Source Camera\', '
                             'example 1: --host_camera_type \'pi_camera\', '
                             'example 1: --host_camera_type \'source_camera\', '
                             'default=\'source_camera\'',
                        type=str,
                        default='source_camera')

    args = parser.parse_args()

    # use your own receiver_server address
    sender = imagezmq.ImageSender(connect_to=args.sender_ip, REQ_REP=False)

    sender_name = socket.gethostname()

    if args.host_camera_type == 'source_camera':
        cam = VideoStream(0).start()
    elif args.host_camera_type == 'pi_camera':
        cam = VideoStream(usePiCamera=True).start()

    time.sleep(2.0)

    try:
        while True:
            image = cam.read()
            sender.send_image(sender_name, image)
    except(KeyboardInterrupt, SystemExit):
        print('Exit due to keyboard interrupt')
    except Exception as ex:
        print('Python error with no Exception handler: ')
        print('Traceback error: ', ex)
        traceback.print_exc()
    finally:
        cam.stop()
        sender.close()
        sys.exit()
