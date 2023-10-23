# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
import sys
from struct import unpack, pack
import time

from concurrent.futures import ThreadPoolExecutor



class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.seq = 0
        self.rec_seq = 0
        self.buffer = {}
        self.mtu = 1469
        self.closed = False
        self.ack = False
        executor = ThreadPoolExecutor(max_workers = 1)
        executor.submit(self.listener)


    def listener(self):
        while not self.closed:
            try:
                data, addr = self.socket.recvfrom()
                
                # continue listening if an empty data packet is received
                # prevents unpack exception: 'requires a buffer of 1472 bytes'
                if data == b'':
                    continue
                
                unpacked = unpack('@Hc1469s', data)
                unpacked_seq_num = unpacked[0]
                is_ack = unpacked[1]

                unpacked_data = unpacked[2].split(b'\x00')[0]

                # stores data in buffer
                if is_ack == b'0':
                    self.buffer[unpacked_seq_num] = unpacked_data
                else:
                    self.ack = True
                # self.recv()
                
            except Exception as e:
                if not self.closed:
                    print("listener died!")
                    print(e)


    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        len = sys.getsizeof(data_bytes)
        
        if len > self.mtu:
            for i in range(0, len, self.mtu):
                if i+self.mtu > len:
                    # 0 for data, 1 for ack
                    data = pack('@Hc1469s', self.seq, b'0', data_bytes[i:len-1])
                    self.socket.sendto(data, (self.dst_ip, self.dst_port))
                else:
                    data = pack('@Hc1469s', self.seq, b'0', data_bytes[i:i+self.mtu])
                    print(type(data))
                    
                    self.socket.sendto(data, (self.dst_ip, self.dst_port))
                self.seq += 1
        else:
            data = pack('@Hc1469s', self.seq, b'0', data_bytes)
            self.socket.sendto(data, (self.dst_ip, self.dst_port))
            self.seq += 1

        while not self.ack: time.sleep(0.01)

        self.ack = False

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""

        total_data = b''

        while self.buffer.get(self.rec_seq):
            total_data += self.buffer[self.rec_seq]

            ack = pack('@Hc1469s', self.rec_seq, b'1', b'')
            self.socket.sendto(ack, (self.dst_ip, self.dst_port))

            self.rec_seq += 1
            
        return total_data
        
        

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        self.closed = True
        self.socket.stoprecv()
        pass
