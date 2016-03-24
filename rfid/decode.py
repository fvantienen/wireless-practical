#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks_cwt

# Some defines that need to be set
tari = 71            # The calculated Tari length
min_rt_th = 0.3      # Minimum amount of distance between peak and -0.5*tari of R->T
min_tr_th = 0.02     # Minimum amount of distance between peak and T->R
tpri = 16.3          # Normaly this can be calculated based on the Query

###### ------------ Code starts here ------------ ######
# Commands
commands = [
    ('00',    'QueryRep',    4,  0 ),
    ('01',    'ACK',         18, 0 ),
    ('1000',  'Query',       22, 5 ),
    ('1001',  'QueryAdjust', 9,  0 ),
    ('1010',  'Select',      44, 16),
    ('11000001',  'Req_RN',  40, 16),
]

# T->R preamble
tr_preamble = [1, 0, 1, 0, 1, 1]

# Main RFID decoder
class RFIDDecoder:
    plt_one = []
    plt_zero = []

    def __init__(self, data):
        self.data = data
        self.data_inv = [-d for d in data]

        # First we find the peaks in the inverted data which could be from the Receiver
        self.trcal = -1
        self.peaks = find_peaks_cwt(self.data_inv, np.arange(1, 0.9*tari))
        self.peaks = [p for p in self.peaks if (self.data[(int)(p - 0.5*tari)] - self.data[p]) > min_rt_th]
        self.cur_peak = 0
        self.peak_cnt = len(self.peaks)

    # Get the bit
    def rt_get_bit(self, p, prev_p):
        if 1.5*tari <= (p - prev_p) <= 2.0*tari:
            return 1
        return 0

    # Find the R->T preamble or sync
    def rt_find_preamble(self):
        # We need at least 3 peaks
        self.cur_peak = max(self.cur_peak, 2)

        # Go trough all peaks
        while self.cur_peak < self.peak_cnt:
            p_data0 = self.peaks[self.cur_peak-2]
            p_rtcal = self.peaks[self.cur_peak-1]
            p_trcal = self.peaks[self.cur_peak]
            rtcal = (p_rtcal - p_data0)
            trcal = (p_trcal - p_rtcal)

            # Check the next peak
            self.cur_peak += 1

            # Check if we got a Frame Sync
            if 2.5*tari <= rtcal <= 3.0*tari:
                self.rtcal = rtcal

                # Check if we got a preamble instead
                if 1.1*rtcal <= trcal <= 3.0*rtcal:
                    self.trcal = trcal
                else:
                    self.cur_peak -= 1
                return True

        # We didn't find a preamble
        return False

    # Decode RT packet
    def rt_decode(self):
        # We go trough the peaks and analyze them
        bits = ""
        cur_command = None
        while self.cur_peak < self.peak_cnt:
            p = self.peaks[self.cur_peak]
            prev_p = self.peaks[self.cur_peak-1] if self.cur_peak > 0 else 0

            # Get the bit
            bit = self.rt_get_bit(p, prev_p)
            bits += str(bit)

            if bit == 1:
                self.plt_one.append(p)
            else:
                self.plt_zero.append(p)

            # Check the next peak
            self.cur_peak += 1

            # Check the current bits for Commands
            if cur_command == None and len(bits) >= 2:
                # Go trough all command and check if bits match
                for command in commands:
                    if command[0] == bits:
                        cur_command = command
                        break

            # Parse the command if finished
            elif cur_command != None and len(bits) >= cur_command[2]:
                real_bits = [int(bit) for bit in bits[len(cur_command[0]):]]
                handler = getattr(self, "handle_%s" % cur_command[1], None)

                if handler:
                    handler(real_bits)
                else:
                    print(cur_command[1] + ": " + bits[2:])

                cur_command = None
                return True

        if len(bits) > 0:
            print("Unknown bits: " + bits)
        return False

    # Get TR bits
    def tr_get_bit(self, peak_val = None):
        start = self.tr_x
        half_tpri = (int)(start+0.5*tpri)
        self.tr_x += tpri

        # Safe the peak value for decoding
        if peak_val != None:
            self.peak_val = peak_val
        else:
            peak_val = self.peak_val

        # Check which state we got
        got_state = 0
        if (peak_val - self.data[(int)(start)]) > min_tr_th and (peak_val - self.data[half_tpri]) > min_tr_th:
            got_state = 1
        elif (peak_val - self.data[(int)(start)]) > min_tr_th and (peak_val - self.data[half_tpri]) < min_tr_th:
            got_state = 2
        elif (peak_val - self.data[(int)(start)]) < min_tr_th and (peak_val - self.data[half_tpri]) > min_tr_th:
            got_state = 3
        elif (peak_val - self.data[(int)(start)]) < min_tr_th and (peak_val - self.data[half_tpri]) < min_tr_th:
            got_state = 4

        # Start state
        if self.tr_state == 0:
            if got_state == 1:
                self.tr_state = got_state
                return 1
        # State 1
        elif self.tr_state == 1:
            if got_state == 4:
                self.tr_state = got_state
                return 1
            elif got_state == 3:
                self.tr_state = got_state
                return 0
        # State 2
        elif self.tr_state == 2:
            if got_state == 1:
                self.tr_state = got_state
                return 1
            elif got_state == 2:
                return 0
        # State 3
        elif self.tr_state == 3:
            if got_state == 4:
                self.tr_state = got_state
                return 1
            elif got_state == 3:
                return 0
        # State 4
        elif self.tr_state == 4:
            if got_state == 1:
                self.tr_state = got_state
                return 1
            elif got_state == 2:
                self.tr_state = got_state
                return 0

        # We didn't got a correct state
        return -1


    # Find TR preamble
    def tr_find_preamble(self):
        p = self.peaks[self.cur_peak - 1]
        peak_val = self.data[(int)(p - 0.75*tari)]
        start = (int)(p + 0.6*tari)
        wait_for_pulse = (int)(10 * tpri)

        # Find the start of the T->R message
        self.tr_x = 0
        for i in range(start, start+wait_for_pulse):
             if (peak_val-self.data[i]) > min_tr_th:
                 self.tr_x = i + 0.25 * tpri
                 break

        # Fetch the preamble
        self.tr_state = 0
        for i in range(0, 6):
            # Fix violation
            if i == 4:
                self.tr_state = 3

            # Check the preamble
            bit = self.tr_get_bit(peak_val)
            if bit != tr_preamble[i]:
                return False

        return True

    # Decode TR message from start
    def tr_decode(self, bits_cnt):
        bits = ""

        # Check if we have a determined amount of bits
        if bits_cnt > 0:
            for i in range(0, bits_cnt):
                bit = self.tr_get_bit()
                # Show it in the graph
                if bit == 1:
                    self.plt_one.append(self.tr_x)
                else:
                    self.plt_zero.append(self.tr_x)

                # Add the bit
                bits += str(bit)
        else:
            while True:
                bit = self.tr_get_bit()
                # Check if it is finished
                if bit < 0:
                    return bits
                else:
                    # Show it in the graph
                    if bit == 1:
                        self.plt_one.append(self.tr_x)
                    else:
                        self.plt_zero.append(self.tr_x)

                    # Add the bit
                    bits += str(bit)
        return bits

    # Handle Query from R->T
    def handle_Query(self, data):
        self.dr = data[0]
        self.trext = data[3]
        print("Query (DR: %d, M: %d%d, TRext: %d, Sel: %d%d)" % (data[0], data[1], data[2], data[3], data[4], data[5]))

    # Handle QueryRep from R->T
    def handle_QueryRep(self, data):
        print("QueryRep (session: %d%d)" % (data[0], data[1]))

    # Handle ACK from R->T
    def handle_ACK(self, data):
        print("ACK (RND16: %s)" % "".join(str(x) for x in data))

        if self.tr_find_preamble():
            print("Response: %s" % self.tr_decode(-1))

    # Handle Req_RN from R->T
    def handle_Req_RN(self, data):
        print("Req_RN (RND16: %s, CRC-16: %s)" % ("".join(str(x) for x in data[:16]), "".join(str(x) for x in data[16:32])))

        if self.tr_find_preamble():
            print("Response: %s" % self.tr_decode(16))

    # Show the plot of data
    def show_plot(self):
        data = np.array(self.data)
        plt.plot(data)                  # Add the data itself

        # Add some debug information
        for x in self.plt_one:
            plt.annotate('1', xy=(x, data[x]), xycoords='data', color='g')
        for x in self.plt_zero:
            plt.annotate('0', xy=(x, data[x]), xycoords='data', color='r')

        plt.show()               # Show the plot

# Main function
def main():
    with open("signal.txt") as f:
        data = map(float, f)

    decoder = RFIDDecoder(data)
    while decoder.rt_find_preamble():
        decoder.rt_decode()
    decoder.show_plot()

if __name__ == "__main__":
    main()
