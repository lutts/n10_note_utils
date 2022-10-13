# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import os
import sys
import http.server
import socket
import contextlib

def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    return family, sockaddr

# ensure dual-stack is not disabled; ref #38907
class DualStackServer(http.server.ThreadingHTTPServer):

    def __init__(self, server_address, RequestHandlerClass, root_directory=None):
        super().__init__(server_address, RequestHandlerClass)
        if not root_directory:
            self.root_directory = os.getcwd()
        else:
            self.root_directory = root_directory

    def server_bind(self):
        # suppress exception when protocol is IPv4
        with contextlib.suppress(Exception):
            self.socket.setsockopt(
                socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        return super().server_bind()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self,
                                    directory=self.root_directory)


def start_http_server(HandlerClass=http.server.SimpleHTTPRequestHandler,
         ServerClass=DualStackServer,
         root_directory=None,
         protocol="HTTP/1.0", port=9999, bind=None):
    """This runs an HTTP server on port 9999 (or the port argument).

    """
    ServerClass.address_family, addr = _get_best_family(bind, port)
    HandlerClass.protocol_version = protocol
    with ServerClass(addr, HandlerClass, root_directory) as httpd:
        host, port = httpd.socket.getsockname()[:2]
        url_host = f'[{host}]' if ':' in host else host
        directory = root_directory if root_directory else "current directory"
        print(
            f"Serving HTTP on {host} port {port} in {directory}\n"
            f"(http://{url_host}:{port}/) ..."
        )
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            sys.exit(0)
