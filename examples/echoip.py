import zmq

ctx = zmq.Context(1)
sock = ctx.socket(zmq.REP)
sock.connect('ipc:///tmp/zmqgate-test-echo_ip')
while True:
    parts = sock.recv_multipart()
    print("GOT", parts)
    sock.send(b"Your ip: " + parts[0])
