import select
import threading
import socketserver
import logging


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            chan = self.ssh_transport.open_channel("direct-tcpip", (self.chain_host, self.chain_port), self.request.getpeername(),)
        except Exception as e:
            logging.debug("Incoming request to %s:%d failed: %s" % (self.chain_host, self.chain_port, repr(e)))
            return
        
        if chan is None:
            logging.debug("Incoming request to %s:%d was rejected by the SSH server." % (self.chain_host, self.chain_port))
            return
        
        logging.debug("Connected! Tunnel open %r -> %r -> %r" % (self.request.getpeername(), chan.getpeername(), (self.chain_host, self.chain_port),))
        self.onConnect(self.request.getpeername())

        try:
            while True:
                r, w, x = select.select([self.request, chan], [], [])
                if self.request in r:
                    data = self.request.recv(1024)
                    if len(data) == 0:
                        break
                    chan.send(data)
                if chan in r:
                    data = chan.recv(1024)
                    if len(data) == 0:
                        break
                    self.request.send(data)
        except Exception:
            pass

        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        
        self.onDisconnect(peername)

#def ssh_forward_tunnel(local_port, remote_host, remote_port, transport):
#    # this is a little convoluted, but lets me configure things for the Handler
#    # object.  (socketserver doesn't give Handlers any way to access the outer
#    # server normally.)
#    class SubHander(Handler):
#        chain_host = remote_host
#        chain_port = remote_port
#        ssh_transport = transport
#
#    #ForwardServer(("", local_port), SubHander).serve_forever()
#    server = ForwardServer(("", local_port), SubHander)
#    server_thread = threading.Thread(target=server.serve_forever)
#    server_thread.daemon = True
#    server_thread.start()
    
class TunServer:
    def __init__(self, local_port, remote_host, remote_port, transport):
        class SubHander(Handler):
            chain_host = remote_host
            chain_port = remote_port
            ssh_transport = transport
            onConnect = self._onConnect
            onDisconnect = self._onDisconnect

        self.onConnect = None
        self.onDisconnect = None
        self.server = socketserver.ThreadingTCPServer(("", local_port), SubHander)
        self.server.allow_reuse_address = True
        self.server.daemon_threads = True
        ## остатки от веб-сервера
        #tcp_socket = socket.socket(self.httpd.address_family, self.httpd.socket_type)
        #self.httpd.socket = ssl.wrap_socket(tcp_socket, self.config.privkeyfile, self.config.pubkeyfile, True)
        #self.httpd.server_bind()
        #self.httpd.server_activate()
        self.server_thread = threading.Thread(target = self.server.serve_forever)
        #self.server_thread.daemon = True
        self.server_thread.start()
        #print('tun start')

    def _onConnect(self, peer):
        logging.debug("Tun: open %r" % (peer,))
        if self.onConnect:
            self.onConnect(peer)
        pass

    def _onDisconnect(self, peer):
        logging.debug("Tun: closed from %r" % (peer,))
        if self.onDisconnect:
            self.onDisconnect(peer)
        pass

    def stop(self):
        self.server.shutdown()
        self.server_thread.join(5)
        self.server.server_close()

