# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
import math
import struct


#chunks are the packets. we want to add a header with sequence numbers and a receive buffer

class Packet:
    #TODO: change this to use the struct class
    def __init__(self, sequence_number, data):
        self.sequence_number = sequence_number
        self.data = data
        self.format_string = "i"+str(len(self.data))+"s"

    def pack(self):
        return struct.pack(self.format_string, self.sequence_number, self.data)

    def unpack(self, packed_data):
        return struct.unpack(self.format_string, packed_data)

class Streamer:
    def __init__(self, dst_ip, dst_port,
                 src_ip=INADDR_ANY, src_port=0):
        """Default values listen on all network interfaces, chooses a random source port,
           and does not introduce any simulated packet loss."""
        self.socket = LossyUDP()
        self.socket.bind((src_ip, src_port))
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.receive_buffer = []

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        # Your code goes here!  The code below should be changed!
        num_chunks = math.ceil(len(data_bytes)/1472)
        print(len(data_bytes))
        for i in range(0, num_chunks):
            chunk = data_bytes[(1472*i):min(1472*(i+1), len(data_bytes) - 1)]

            #create the packet
            packet = Packet(i, chunk)

            #Pack it into a struct 
            packet = packet.pack()
            print(packet)
            
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""
        next_expected_seq_no = 0
        
        # this sample code just calls the recvfrom method on the LossySocket
        data, addr = self.socket.recvfrom()

        # unpack the data here
        
        # If sequence number is greater than next expected, add it to the receive buffer

        # If sequence number == next_expected, return it and updated the value

        # Receive the next in order segments and updated next_expected

        # For now, I'll just pass the full UDP payload to the app
        return data

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.
        pass
