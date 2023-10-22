# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
import sys
from struct import unpack, pack

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
        self.mtu = 1470
        self.closed = False
        executor = ThreadPoolExecutor(max_workers = 1)
        executor.submit(self.listener)

        #


    def listener(self):
        while not self.closed:
            try:
                data, addr = self.socket.recvfrom()
                
                # continue listening if an empty data packet is received
                # prevents unpack exception: 'requires a buffer of 1472 bytes'
                if data == b'':
                    continue
                
                unpacked = unpack('@H1470s', data)
                unpacked_seq_num = unpacked[0]
                unpacked_data = unpacked[1].split(b'\x00')[0]

                # stores data in buffer
                self.buffer[unpacked_seq_num] = unpacked_data
                # self.recv()
                
            except Exception as e:
                print("listener died!")
                print(e)


    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        len = sys.getsizeof(data_bytes)
        # print(len)
        # print(data_bytes)
        
        
        # j = 0
        if len > self.mtu:
            for i in range(0, len, self.mtu):
                if i+self.mtu > len:
                    data = pack('@H1470s', self.seq, data_bytes[i:len-1])
                    self.socket.sendto(data, (self.dst_ip, self.dst_port))
                else:
                    data = pack('@H1470s', self.seq, data_bytes[i:i+self.mtu])
                    print(type(data))
                    
                    self.socket.sendto(data, (self.dst_ip, self.dst_port))
                self.seq += 1
        else:
        # for now I'm just sending the raw application-level data in one UDP payload
            data = pack('@H1470s', self.seq, data_bytes)
            # print(type(data))
            self.socket.sendto(data, (self.dst_ip, self.dst_port))
            self.seq += 1

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        # your code goes here!  The code below should be changed!
        
        # this sample code just calls the recvfrom method on the LossySocket
        


        # data, addr = self.socket.recvfrom()
        # size = sys.getsizeof(data)
        # unpacked = unpack('@H1470s', data)


        # unpacked_seq_num = unpacked[0]
        # unpacked_data = unpacked[1].split(b'\x00')[0]
        # size = sys.getsizeof(unpacked_data)
        

        # if we receive an unpacked_seq_num out of order (!= rec_seq)
        # we store it in buffer as key w value data
        # when 
        # print(unpacked_data)
        # print(type(unpacked_seq_num))
        # print(type(self.rec_seq))

        if self.buffer.get(self.rec_seq):
            total_data = self.buffer[self.rec_seq]

            while self.buffer.get(self.rec_seq + 1) != None:
               total_data += self.buffer[self.rec_seq + 1]
               self.rec_seq += 1
            
            self.rec_seq += 1
            print(total_data)
            return total_data
        
        # print(f"TYPE: {type(data)}")
        # print(f"DATA: {data}")
        # print(f"Unpacked DATA: {unpacked_data}")
        
        # For now, I'll just pass the full UDP payload to the app
        return b''

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        self.closed = True
        self.socket.stoprecv()
        pass
