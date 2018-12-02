# -*- coding: utf-8 -*-
#
# This file is part of PyGaze - the open-source toolbox for eye tracking
#
#    PyGaze is a Python module for easily creating gaze contingent experiments
#    or other software (as well as non-gaze contingent experiments/software)
#    Copyright (C) 2012-2018 Edwin S. Dalmaijer
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>

import os
import copy
import time
from ctypes import windll, c_int, c_double, byref
from threading import Thread, Lock

import numpy


# Load BIOPAC's mpdev DLL.
try:
    mpdev = windll.LoadLibrary('mpdev.dll')
except:
    try:
        mpdev = windll.LoadLibrary(os.path.join(os.path.dirname(os.path.abspath(__file__)),'mpdev.dll'))
    except:
        raise Exception("Error in mpydev: could not load mpdev.dll")


# Function to handle errors from the mpdev DLL functions.
def check_returncode(returncode):

    """
    desc:
        Checks a BioPac MP150 returncode, and returns it's meaning as a human 
        readable string.

    arguments:
        returncode:
            desc:    A code returned by one of the functions from the mpdev DLL
            type:    int

    returns:
        desc:    A string describing the error
        type:    str
    """

    if returncode == 1:
        meaning = "MPSUCCESS"
    else:
        meaning = "UNKNOWN"

    return meaning


# class definition
class BioPac:
    
    """
    desc:
        Class to communicate with BIOPAC devices such as the MP150, MP160, and
        MP36R. This class works through mpdev.dll, which should be installed
        separately.
    """
    
    def __init__(self, devname, n_channels=3, samplerate=200, \
        logfile='default', overwrite=False):
        
        """
        desc:
            Finds a BioPac device, and initializes a connection.
        
        arguments:
            devname:
                desc: Name of the device that should be connected, e.g. 
                    "MP150", "MP160", or "MP36R"
                type: str
        
        keywords:
            n_channels:
                desc: The number of channels that should be recorded from.
                    Default = 3
                type: int
            samplerate:
                desc: The sampling rate in Hertz (default = 200)
                type: int
            logfile:
                desc: Name of the logfile (optionally with path), which will
                    be used to create a textfile, e.g.
                    'default_BIOPAC_data.tsv' (default = 'default')
                type:str
            overwrite:
                desc: Indicates whether the log file should be overwritten if
                    a file with the same name already exists. (default = False)
                type: bool
        """
        
        # Dict with the supported devices and their codes.
        self._supported = { \
            "MP150":    101, \
            "MP160":    103, \
            "MP36R":    103, \
            }
        
        # Check whether the passed device name is valid.
        if devname.upper() not in self._supported.keys():
            raise Exception("ERROR in mpydev: Unknown device name '%s'. Supported devices are: %s" \
                % (devname, self._supported.keys()))

        # Set the device name and code properties.
        self._devname = devname.upper()
        self._devcode = self._supported[self._devname]

        # Set the sampling properties.
        self._samplerate = float(samplerate)
        self._sampletime = 1000.0 / self._samplerate
        self._sampletimesec = self._sampletime / 1000.0
        
        # Check the channels, and verify that there aren't over 16.
        if n_channels > 0 and n_channels <= 16:
            self._n_channels = int(n_channels)
        else:
            raise Exception("ERROR in mpydev: 1-16 channels can be recorded; you requested %d channels" \
                % (int(n_channels)))
        
        # Set the log file name.
        self._logfilename = "%s_BIOPAC_data.tsv" % (logfile)
        # Check if the logfile already exists.
        if os.path.isfile(self._logfilename) and not overwrite:
            # Find a file name that isn't used yet by incrementing a number.
            i = 1
            while os.path.isfile(self._logfilename):
                i += 1
                self._logfilename = "%s_%d_BIOPAC_data.tsv" % (i, logfile)
        
        # Pre-create properties that are used by methods.
        self._newestsample = numpy.zeros(n_channels, dtype=float)
        self._buffer = []
        self._buffch = 0
        
        # Connect to the BIOPAC device. The first passed variable is the
        # device code (101 for MP150, 103 for MP160 or MP36R), the second
        # passed variable is for the communication method (11), and the third
        # argument is for the way to connect to a device ('auto' is for 
        # automatically connecting to the first responding device).
        try:
            result = mpdev.connectMPDev(c_int(self._devcode), c_int(11), b'auto')
        except:
            result = "failed to call connectMPDev"
        if check_returncode(result) != "MPSUCCESS":
            raise Exception("Error in mpydev: failed to connect to the device: %s" \
                % (result))
        
        # Get the connection start time.
        self._starting_time = time.time()
        
        # Set the device's sampling rate.
        try:
            result = mpdev.setSampleRate(c_double(self._sampletime))
        except:
            result = "failed to call setSampleRate"
        if check_returncode(result) != "MPSUCCESS":
            raise Exception("Error in mpydev: failed to set samplerate: %s" \
                % (result))
        
        # Set Channels to acquire.
        try:
            # Create a total of 16 channels, with the requested amount set to 
            # on (1), and the others set to off (0).
            channels = self._n_channels * [1]
            channels.extend((16-self._n_channels) * [0])
            # Convert the channel list into a c_int_Array.
            channels = (c_int * len(channels))(*channels)
            # Set the channels through mpdev.
            result = mpdev.setAcqChannels(byref(channels))
        except:
            result = "failed to call setAcqChannels"
        if check_returncode(result) != "MPSUCCESS":
            raise Exception("Error in mpydev: failed to set channels to acquire: %s" \
                % (result))
        
        # Start data acquisition.
        try:
            result = mpdev.startAcquisition()
        except:
            result = "failed to call startAcquisition"
        if check_returncode(result) != "MPSUCCESS":
            raise Exception("Error in mpydev: failed to start acquisition: %s" \
                % (result))
        
        # Open a new log file.
        self._logfile = open(self._logfilename, 'w')
        # Write a header to the logfile.
        header = ["timestamp"]
        header.extend(["channel_%d" % i for i in range(self._n_channels)])
        self._logfile.write("\t".join(header))
        
        # Create logging lock to prevent simultaneous access to the lof file
        # from different Threads.
        self._loglock = Lock()
        
        # Start the sample processing Thread. This will run int the background
        # to collect and optionally log samples.
        self._recording = False
        self._recordtobuff = False
        self._connected = True
        self._spthread = Thread(target=self._sampleprocesser)
        self._spthread.daemon = True
        self._spthread.name = "sampleprocesser"
        self._spthread.start()
    
    
    def start_recording(self):
        
        """
        desc:
            Starts writing MP150 samples to the log file.
        """
        
        # Signal to the sample processing thread that recording is active.
        self._recording = True
    
    
    def stop_recording(self):
        
        """
        desc:
            Stops writing MP150 samples to the log file.
        """
        
        # Signal to the sample processing thread that recording stopped.
        self._recording = False

        # Consolidate logged data from the internal buffer to disk.
        self._loglock.acquire(True)
        # Internal buffer to RAM.
        self._logfile.flush()
        # # RAM file cache to disk.
        os.fsync(self._logfile.fileno())
        self._loglock.release()
    
    
    def start_recording_to_buffer(self, channel=0):
        
        """
        desc:
            Starts recording to an internal buffer.
        
        keywords:
            channel:
                desc: The channel from which needs to be recorded.
                    (default = 0)
                type: int
        """
        
        # Clear the internal buffer.
        self._buffer = []
        self._buffch = channel
        
        # Signal to the sample processing thread that recording to the internal
        # buffer is active.
        self._recordtobuff = True
    
    
    def stop_recording_to_buffer(self):
        
        """
        desc:
            Stops recording samples to an internal buffer.
        """
        
        # Signal to the sample processing thread that recording stopped.
        self._recordtobuff = False

    
    def sample(self):
        
        """
        desc:
            Returns the most recent sample provided by the BIOPAC device.
        
        returns:
            desc: The latest BIOPAC output values for the requested channels,
                as a list of floats.
            type: list
        """
        
        return self._newestsample

    
    def get_buffer(self):
        
        """
        desc:
            Returns the internal sample buffer, which is filled up when
            start_recording_to_buffer is called. This function is
            safest to call only after stop_recording_to_buffer is called
        
        returns:
            desc: A NumPy array containing samples from since
                start_recording_to_buffer was last called, until
                get_buffer or stop_recording_to_buffer was called
            type: numpy.array
        """
        
        return numpy.array(self._buffer)

    
    def log(self, msg):
        
        """
        desc:
            Writes a message to the log file.
        
        arguments:
            msg:
                desc: The message that is to be written to the log file.
                type: str
        """
        
        # Get the call timestamp.
        t = self.get_timestamp()
        
        # Wait for the logging lock to be released, then lock it.
        self._loglock.acquire(True)
        
        # Log the message, including the recorded timestamp.
        self._logfile.write("\nMSG\t%d\t%s" % (t, msg))
        
        # Release the logging lock.
        self._loglock.release()

    
    def close(self):
        
        """
        desc:
            Closes the connection to the BIOPAC device.
        """
        
        # Stop recording if it's still on.
        if self._recording:
            self.stop_recording()
        # Close the log file.
        self._logfile.close()
        # Signal to the sample processing Thread that it can stop.
        self._connected = False
        
        # Close the connection with the BIOPAC device.
        try:
            result = mpdev.disconnectMPDev()
        except:
            result = "failed to call disconnectMPDev"
        if check_returncode(result) != "MPSUCCESS":
            raise Exception("Error in mpydev: failed to close the connection to the BIOPAC: %s" \
                % (result))

    
    def get_timestamp(self):
        
        """
        desc:
            Returns the time in milliseconds since the connection was opened
        
        returns:
            desc: Time (milliseconds) since connection was opened
            type: int
        """
        
        return int((time.time()-self._starting_time) * 1000)
    
    
    def _sampleprocesser(self):
        
        """
        desc:
            Processes samples while self._recording is True (INTERNAL USE!)
        """
        
        # Run until the connection is closed.
        while self._connected:
            # Attempt to get a new sample from the BIOPAC.
            try:
                # Start with a list of 0s.
                data = self._n_channels * [0.0]
                # Convert the list to a c_double_Array.
                data = (c_double * len(data))(*data)
                # Get the most recent sample from the BIOPAC.
                result = mpdev.getMostRecentSample(byref(data))
                # Get a timestamp.
                t = self.get_timestamp()
                # Convert the returned array into a tuple.
                data = tuple(data)
            # Throw a fit when data could not be obtained.
            except:
                result = "failed to call getMPBuffer"
            if check_returncode(result) != "MPSUCCESS":
                raise Exception("Error in mpydev: failed to obtain a sample from the MP150: %s" % result)

            # Check if the new sample is in fact new.
            if data != self._newestsample:
                # Update the internal newest sample.
                self._newestsample = copy.deepcopy(data)

                # Write the new sample to file.
                if self._recording:
                    # Collect the data into a single list.
                    line = [t]
                    line.extend(data)
                    # Wait for the logging lock to be released, then lock it.
                    self._loglock.acquire(True)
                    # Log the data as a string of tab-separated values.
                    self._logfile.write("\n" + "\t".join(map(str, line)))
                    # Release the logging lock.
                    self._loglock.release()

                # Add the sample to the buffer.
                if self._recordtobuff:
                    self._buffer.append(self._newestsample[self._buffch])

            # Pause until the next sample is available.
            # This is commented out, because it is currently unnecessary: 
            # getMostRecentSample blocks until a new sample is available, so
            # we don't have to manually wait. If it wouldn't block, waiting
            # for a bit would be advantageous, as it avoids wasting computing
            # resources on continuously checking whether a new sample is
            # available.
            #time.sleep(self._sampletimesec)
