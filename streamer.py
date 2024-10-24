# do not import anything else from loss_socket besides LossyUDP
from lossy_socket import LossyUDP
# do not import anything else from socket except INADDR_ANY
from socket import INADDR_ANY
import math
import struct
from concurrent.futures import ThreadPoolExecutor


#chunks are the packets. we want to add a header with sequence numbers and a receive buffer

class Packet:
    #TODO: change this to use the struct class
    def __init__(self, sequence_number, data):
        self.sequence_number = sequence_number
        self.data = data
        self.format_string = "i"+str(len(self.data))+"s"
        self.packed_len = struct.pack("i",len(self.data))

    def pack(self):
        #pack data using format string with a length prefix
        return self.packed_len +struct.pack(self.format_string, self.sequence_number, self.data)

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
        self.sequence_no = 0
        self.next_expected_seq_no = 0
        # The packet size is the max size of packets minus the size of two ints
        self.packet_size = 1472 - 8 

        #Start the listener function in a background thread using concurrent futures
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.listener)

    def send(self, data_bytes: bytes) -> None:
        """Note that data_bytes can be larger than one packet."""
        num_chunks = math.ceil(len(data_bytes)/self.packet_size)
        print(len(data_bytes))

        for i in range(0, num_chunks):
            chunk = data_bytes[(self.packet_size*i):min(self.packet_size*(i+1), len(data_bytes) - 1)]

            #create the packet
            packet = Packet(self.sequence_no, chunk)

            #Pack it into a struct 
            packet = packet.pack()
            # print(packet)

            self.sequence_no += 1
            
            self.socket.sendto(packet, (self.dst_ip, self.dst_port))

    def recv(self) -> bytes:
        """Blocks (waits) if no data is ready to be read from the connection."""

        print("buffer ", self.receive_buffer)
        for packet in self.receive_buffer:
            if packet[0] == self.next_expected_seq_no:
                result = packet[1]
                self.receive_buffer.remove(packet)
                self.next_expected_seq_no += 1
                return result

        # this sample code just calls the recvfrom method on the LossySocket
        data, addr = self.socket.recvfrom()

        # unpack the data here
        print("Packed data received ", data)
        #source: https://stackoverflow.com/questions/3753589/packing-and-unpacking-variable-length-array-string-using-the-struct-module-in-py
        length, seq_no = struct.unpack("ii", data[:8])
        data = data[8:]
        
        print("Length: ", length, "seq: ", seq_no)
        print("data ", data)

        # If sequence number == next_expected, return it and updated the value
        if seq_no == self.next_expected_seq_no:
            self.next_expected_seq_no += 1
            return data

        # If sequence number is greater than next expected, add it to the receive buffer and re run this function
        else:
            self.receive_buffer.append([seq_no, data])
            return self.recv()
            
        return

    def listener(self):
        while not self.closed: # a later hint will explain self.closed
            print("inside listener")
            try:
                data, addr = self.socket.recvfrom()
                
                # store the data in the receive buffer
                length, seq_no = struct.unpack("ii", data[:8])
                data = data[8:]
                self.receive_buffer.append([seq_no, data])
            
            except Exception as e: 
                print("listener died!")
                print(e)

    def close(self) -> None:
        """Cleans up. It should block (wait) until the Streamer is done with all
           the necessary ACKs and retransmissions"""
        # your code goes here, especially after you add ACKs and retransmissions.

        self.closed = True
        self.socket.stoprecv()
