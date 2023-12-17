"""
TDTendec - Tonal Data Transmission Encoder/Decoder, Version 1.12.17
(c) 2023 Vyacheslav "VyaCHACHsel" Kirnos, All rights reserved.
Based on "Frequency Shift Keying in Python"
Copyright (c) 2023 Joey Manani
License found at https://cdn.theflyingrat.com/LICENSE.txt
Permission is hereby granted to modify, copy and use this app as per the license WITH credit to me and a link to the license
"""


import math
import wave
import struct
import numpy as np
from colorama import Fore, Style, just_fix_windows_console
from scipy.fft import rfft, rfftfreq
import argparse
import operator
import os
import traceback
from alive_progress import alive_bar
import platform as plat

class FrequencyShiftKeying:
    """Generate a wave file containing FSK encoded data."""
    def __init__(self, duration: int, sample_rate: int):
        # self._high_frequency = 1000
        # self._low_frequency = 500
        self._11_freq = 2000
        self._10_freq = 1750
        self._div_freq = 1500 # This frequency signifies the boudry between a pair of bytes.
        self._01_freq = 1250
        self._00_freq = 1000
        self._amplitude = 32767  # 16 bit unsigned wave maximum amplitude
        self._duration = duration  # Duration in samples per tone
        self._sample_rate = sample_rate
        self._global_signal = []  # Samples where wave file is stored


    # https://stackoverflow.com/questions/48043004/how-do-i-generate-a-sine-wave-using-python
    def _create_sine_wave(self, frequency: int, phase: float) -> float:
        """Create a sine wave of given frequency and append it to global_signal

        :param frequency: Frequency in hertz
        :param phase: phase at which start the wave
        :return: the phase of the current point of the sine wave (from 0 to 1).
        """
        signal = []
        num_samples = self._duration

        for i in range(num_samples):
            value = self._amplitude * math.sin(2 * math.pi * frequency * (i + (phase * self._sample_rate) / frequency) / self._sample_rate)
            signal.append(value)

        self._global_signal.extend(signal)
        
        # Don't ask me how the calculation on return works, it just works.
        # To come up with this formula I was sitting with a calculator for 3 hours, & I had long forgot what do those variables do...
        return (self._duration * frequency / self._sample_rate) + phase - int((self._duration * frequency / self._sample_rate) + phase)


    def encode(self, binary_bits: list, filename: str) -> None:
        """Encode the data given as...

        :param binary_bits: an iterable of binary bits
        :raises ValueError: if any binary digit is not 0 or 1 (as integers)
        """
        
        # nice bar starting
        with alive_bar(math.floor(len(binary_bits)/16)+1, bar = 'smooth', spinner = 'waves') as bar:
            bar.title("Encoding...")
            bar.text('Header generation')
            global phase
            phase = 0.0
            two_bits = ""
            bytecounter = 0
            i = 16
            while i > 0:
                i-=1
                phase = self._create_sine_wave(self._11_freq, phase)
                
            i=16
            while i > 0:
                i-=1
                phase = self._create_sine_wave(self._div_freq, phase)
                
            i=16
            while i > 0:
                i-=1
                if i % 2 == 0:
                    phase = self._create_sine_wave(self._11_freq, phase)
                if i % 2 == 1:
                    phase = self._create_sine_wave(self._00_freq, phase)
                    
            i=4
            while i > 0:
                i-=1
                phase = self._create_sine_wave(self._div_freq, phase)
                
            output_wave = wave.open(filename, 'w')
            output_wave.setparams((1,
                                   2,
                                   self._sample_rate,
                                   len(self._global_signal),
                                   'NONE',
                                   'not compressed'
                                   ))
                                   
            for value in self._global_signal:
                packed_value = struct.pack('h', int(value))
                output_wave.writeframes(packed_value)
            
            self._global_signal=[]
            
            bar.text('Encoding data')
            
            for bit in binary_bits:
                two_bits += str(bit)
                bytecounter += 1
                #print("two_bits = ", two_bits, "; bytecounter = ", bytecounter)
                if two_bits == "11":
                    phase = self._create_sine_wave(self._11_freq, phase)
                    two_bits = ""
                elif two_bits == "10":
                    phase = self._create_sine_wave(self._10_freq, phase)
                    two_bits = ""
                elif two_bits == "01":
                    phase = self._create_sine_wave(self._01_freq, phase)
                    two_bits = ""
                elif two_bits == "00":
                    phase = self._create_sine_wave(self._00_freq, phase)
                    two_bits = ""
                elif len(two_bits) >= 2:
                    bar.title("AAAAAAAAAAA")
                    raise ValueError("Invalid bit value")
                if bytecounter == 16:
                    phase = self._create_sine_wave(self._div_freq, phase)
                    bytecounter = 0
                    #print("division!")
                    for value in self._global_signal:
                        packed_value = struct.pack('h', int(value))
                        output_wave.writeframes(packed_value)
                    
                    self._global_signal=[]
                    bar()
                    
            bar.text('Tail')
            
            i=4
            while i > 0:
                i-=1
                phase = self._create_sine_wave(self._div_freq, phase)
                
            for value in self._global_signal:
                packed_value = struct.pack('h', int(value))
                output_wave.writeframes(packed_value)
                
            bar()
            
            bar.title("C'est fini!")


    def decode(self) -> list:
        """Decode imported wave signal

        :raises ValueError: if a bad frequency is detected. Duration of tone may be too short 
        :return: Decoded data as a list of bits
        """
        binary_data = []
        samples_per_tone = self._duration * 2 # no idea why this works but it does.
        num_samples = len(self._global_signal) #// 2  # Dividing by 2 to work with stereo signal
        num_tones = num_samples // samples_per_tone # FSK tones (or bits) in the file

        if num_samples == 0 or num_tones == 0:
            raise ValueError("Could not find any samples to decode!")
            
        preamble = 0
        sync = []

        for i in range(num_tones):
            start_idx = i * samples_per_tone# * 2  # Multiply by 2 for stereo signal
            end_idx = start_idx + samples_per_tone# * 2
            tone_samples = self._global_signal[start_idx:end_idx]

            # Convert tone_samples to mono and calculate frequency
            tone_samples_mono = np.frombuffer(tone_samples, dtype=np.int16)
            freq = self._get_frequency(tone_samples_mono)

            # Test if calculated frequency is 10% of expected frequency
            # https://www.w3schools.com/python/ref_math_isclose.asp
            
            # Transmission should start from a 11 signal
            if preamble == 0 and math.isclose(freq, self._11_freq, rel_tol=0.1):
                preamble = 1
            
             # Followed by a byte division signal...
            if preamble == 1 and math.isclose(freq, self._div_freq, rel_tol=0.1):
                preamble = 2
            
            # ... & then a preamble: 16 alterating 11 & 00 tones
            if preamble == 2 and math.isclose(freq, self._11_freq, rel_tol=0.1):
                sync.append(1)
            if preamble == 2 and math.isclose(freq, self._00_freq, rel_tol=0.1):
                sync.append(0)
            
            # The neat decode stuff:
            if preamble == 3:
                if math.isclose(freq, self._11_freq, rel_tol=0.1):
                    binary_data.append(1)
                    binary_data.append(1)
                elif math.isclose(freq, self._10_freq, rel_tol=0.1):
                    binary_data.append(1)
                    binary_data.append(0)
                elif math.isclose(freq, self._01_freq, rel_tol=0.1):
                    binary_data.append(0)
                    binary_data.append(1)
                elif math.isclose(freq, self._00_freq, rel_tol=0.1):
                    binary_data.append(0)
                    binary_data.append(0)
                elif math.isclose(freq, self._div_freq, rel_tol=0.1):
                    while (len(binary_data) % 16) > 0: # if we get division frequency while the 2 bytes aren't complete, fill the rest with zeros.
                        binary_data.append(0)
                        binary_data.append(0)
                else: # if we have no idea what frequency is this, just write two zeros.
                    binary_data.append(0)
                    binary_data.append(0)
                    
                # Past implementation stopped the entire process if some frequency isn't recognized.
                # I write pairs of bits in confusing situations because there's no way a singular zero can be written.
            
            # Sync check:
            if preamble == 2 and len(sync) == 16:
                if sync == [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]: # this is how bytes are ordered
                    preamble = 3
                else: # If the sync is not correct, don't bother decoding the signal - that's probably not what you're looking for...
                    raise ValueError("Bad header sync")

        return binary_data


    # https://stackoverflow.com/questions/54612204/trying-to-get-the-frequencies-of-a-wav-file-in-python
    # https://realpython.com/python-scipy-fft/
    def _get_frequency(self, samples: np.ndarray) -> float:
        """Gets a frequency from ndarray samples

        :param samples: Numpy ndarray representation of wave samples
        :return: Frequency in hertz
        """

        # No clue how this works to be honest. I don't like math.
        # I think it calculates how many peaks of the samples are within 1/sample_rate samples?
        # I could be entirely wrong
        number_of_samples = len(samples)
        yf = rfft(samples)
        xf = rfftfreq(number_of_samples, 1 / self._sample_rate)
        idx = np.argmax(np.abs(yf))
        frequency = xf[idx]
        return frequency


    def save_to_wave_file(self, filename: str) -> None:
        """Save global signal to a wave file

        :param filename: File name to save the global signal under
        """
        output_wave = wave.open(filename, 'w')
        output_wave.setparams((1,
                               2,
                               self._sample_rate,
                               len(self._global_signal),
                               'NONE',
                               'not compressed'
                               ))

        for value in self._global_signal:
            packed_value = struct.pack('h', int(value))
            output_wave.writeframes(packed_value)

        output_wave.close()


    # https://stackoverflow.com/questions/2060628/reading-wav-files-in-python
    def load_from_wave_file(self, filename: str) -> list:
        """Load a wave file from disk and return decode it 

        :param filename: The filename to open and load to the global signal
        """
        input_wave = wave.open(filename, 'r')
        signal = input_wave.readframes(-1)
        input_wave.close()

        self._global_signal = signal




if __name__ == "__main__":
    print(f'{Style.BRIGHT}{Fore.CYAN}TDTendec - Tonal Data Transmission Encoder/Decoder{Fore.YELLOW} V.1.12.17\n{Fore.BLACK}(c) 2023 Vyacheslav "VyaCHACHsel" Kirnos, All rights reserved.\nBased on "Frequency Shift Keying in Python" (c) 2023 Joey Manani\n\n{Fore.RESET}{Style.NORMAL}{Fore.CYAN}')
    parser = argparse.ArgumentParser(prog='TDTendec',description='This program is used to encode and decode data using Tonal Data Transmission (TDT).', usage='%(prog)s --encode/--decode audiofile datafile mode')
    parser.add_argument('-e','--encode', action='store_const', const=True, default=False, help='Encode the data into an audio file.')
    parser.add_argument('-d','--decode', action='store_const', const=True, default=False, help='Decode the audio file into data.')
    parser.add_argument('audiofile', default="", help='An audio file (to be) containing encoded information. Should only be in RIFF *.wav format.')
    parser.add_argument('datafile', default="", help='A file (to be) containing decoded/to be encoded information. Can be literally anything, but the larger is the file, the longer the transfer is and the bigger is the audio file.')
    #parser.add_argument('mode', default="", help='Specifies the mode used. Can be one of the following: TDT-11, TDT-22, TDTH4-22, TDTH4-40, TDTH8-40.')
    try:
        args = parser.parse_args()
        #print("Successfully parsed args: ", args)
        if operator.xor(args.encode, args.decode) == 0:
            raise ValueError("misuse of --encode and --decode args: please use only one of them.")
        try:
            print(f'{Fore.RESET}Preparing the library...')
            fsk = FrequencyShiftKeying(duration=375, sample_rate=12000)
            #print("debug: audiofile name getting")
            audiofile = args.audiofile
            #print("debug: opening datafile")
            if plat.system() == 'Windows':
                datafile = os.open(args.datafile, os.O_RDWR + os.O_BINARY + os.O_CREAT)
            else:
                datafile = os.open(args.datafile, os.O_RDWR + os.O_CREAT)
            #print("debug: datafile == ", datafile)
        
            if args.decode == True:
                fsk.load_from_wave_file(audiofile) # Open the wave file
                DECODED_BITS = fsk.decode() # Decode the wave file
        
                BIT_STRING = ''.join(map(str, DECODED_BITS)) # [0,1,1,0] --> "0110"
                BIT_CHUNKS = [BIT_STRING[i:i+8] for i in range(0, len(BIT_STRING)-16, 8)] # 8 bits to byte
                ASCII_TEXT = ''.join(chr(int(chunk, 2)) for chunk in BIT_CHUNKS) # "01000001" --> "A"
                os.write(datafile, bytes(int(chunk, 2) for chunk in BIT_CHUNKS))

                print(f"{Style.DIM}{Fore.YELLOW}Encoded bits: {Fore.CYAN}", BIT_STRING)
                print(f"{Fore.YELLOW}Decoded text: {Fore.CYAN}", ASCII_TEXT) # ASCII decoded text
                
            if args.encode == True:
                DATA = os.read(datafile, os.fstat(datafile).st_size)
                if len(DATA) % 2 == 1:
                    DATA = DATA + bytes.fromhex('00')
                DATA = DATA + bytes.fromhex('ffff')
                raw_bits = []
                for byte in DATA:
                    raw_bits.extend(int(bit) for bit in bin(byte)[2:].zfill(8)) # Create bits from bytes

                fsk.encode(raw_bits, audiofile) # Encode the bits into wave
                #print("Saving...")
                #fsk.save_to_wave_file(audiofile) # Save the wave file

                print("\nEncoded data: ", DATA)
                print('\n\nThere is a file "',audiofile,'" which contains the TDT encoded data')
                
            os.close(datafile)

        except Exception as e:
            print(f"{Style.BRIGHT}{Fore.RED}An error occurred: {Fore.RESET}{e}")
            print(f"\n\n{Fore.BLACK}Maybe press printscreen and send to the dev?..")
    except ValueError as e:
        print(f"{Style.BRIGHT}{Fore.RED}Arrgument error: {Style.RESET_ALL}{e}")
        traceback.print_exc(e.__traceback__)
        print(f"\n")
        parser.print_usage()
        print(f'{Fore.CYAN}No idea? Try "TDTendec -h"!')
    finally:
        print(f"{Style.RESET_ALL}\n*** END")