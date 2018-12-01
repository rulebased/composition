import argparse
import zmq

def main():
    parser = argparse.ArgumentParser(description='Allocate simulation jobs among workers')
    parser.add_argument('-c', '--client', dest="client", default="tcp://*:9898", help="Server side of queue")
    parser.add_argument('-s', '--server', dest="server", default="tcp://*:9899", help="Server side of queue")
    args = parser.parse_args()

    try:
        context = zmq.Context(1)
        # Socket facing clients
        frontend = context.socket(zmq.XREP)
        frontend.bind(args.client)
        # Socket facing services
        backend = context.socket(zmq.XREQ)
        backend.bind(args.server)

        zmq.device(zmq.QUEUE, frontend, backend)
    except Exception as e:
        print(e)
        print("bringing down zmq device")
    finally:
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    main()
