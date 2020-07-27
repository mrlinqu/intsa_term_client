#!/usr/bin/env python

import socket
import select
import threading
import logging


# def handler(chan, host, port):
#     sock = socket.socket()
#     try:
#         sock.connect((host, port))
#     except Exception as e:
#         logging.debug("Forwarding request to %s:%d failed: %r" % (host, port, e))
#         return

#     logging.debug("Connected!  Tunnel open %r -> %r -> %r" % (chan.origin_addr, chan.getpeername(), (host, port)))

#     while True:
#         r, w, x = select.select([sock, chan], [], [])
#         if sock in r:
#             data = sock.recv(1024)
#             if len(data) == 0:
#                 break
#             chan.send(data)
#         if chan in r:
#             data = chan.recv(1024)
#             if len(data) == 0:
#                 break
#             sock.send(data)
#     chan.close()
#     sock.close()
    
#     logging.debug("Tunnel closed from %r" % (chan.origin_addr,))

#     pass


# def handler1(chan, origin_addr, server_addr):
#     logging.debug("Reverse tunnel open %r -> %r" % (origin_addr, server_addr))
    
#     sock = socket.socket()
#     try:
#         sock.connect((host, port))
#     except Exception as e:
#         logging.debug("Reverse forwarding request to %s:%d failed: %r" % (host, port, e))
#         return

#     chan.close()

#     pass


# #def rforward(server_port, remote_host, remote_port, transport):
# def rforward(server, port, transport):
#     transport.request_port_forward(address=server, port=port, handler=handler1)
#     # while True:
#     #     chan = transport.accept(1000)
        
#     #     if chan is None:
#     #         continue

#     #     thr = threading.Thread(target=handler, args=(chan, remote_host, remote_port))
#     #     thr.setDaemon(True)
#     #     thr.start()

#     pass




class RForvard(threading.Thread):
    def __init__(self, transport, remote_addr, remote_port, server_addr, server_port):
        super(RForvard, self).__init__()

        self.transport = transport
        self.remote_host = remote_addr
        self.remote_port = remote_port
        self.server_addr = server_addr
        self.server_port = server_port
        #    server_thread = threading.Thread(target=server.serve_forever)
        #    server_thread.daemon = True
        #    server_thread.start()

        self.is_alive = False

        pass

    def run(self):
        logging.debug("Reverse forwarding request wait starting %s:%s" % (self.server_addr,self.server_port,))
        self.is_alive = True
        self.transport.request_port_forward(address=self.server_addr, port=self.server_port)
        while self.is_alive:
            chan = self.transport.accept(1)
            
            if chan is None:
                continue

            #thr = threading.Thread(target=handler, args=(chan, self.remote_host, self.remote_port))
            thr = threading.Thread(target=self.handler, args=(chan, self.remote_host, self.remote_port))
            thr.setDaemon(True)
            thr.start()
        
        logging.debug("Reverse forwarding request wait stoped")

        pass

    def handler(self, chan, host, port):
        sock = socket.socket()
        try:
            sock.connect((host, port))
        except Exception as e:
            logging.debug("Reverse forwarding request to %s:%d failed: %r" % (host, port, e))
            return

        logging.debug("Connected! Reverse tunnel open %r -> %r -> %r" % (chan.origin_addr, chan.getpeername(), (host, port)))

        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)
        chan.close()
        sock.close()
        
        logging.debug("Reverse tunnel closed from %r" % (chan.origin_addr,))
        pass

    def stop(self):
        self.is_alive = False
        self.transport.cancel_port_forward(address=self.server_addr, port=self.server_port)
        pass

    pass
