#!/usr/bin/env python
# coding: utf-8

# In[11]:


deviceName = "/dev/co2mini7"
logFile = "./minmonlog.csv"
secondsBetweenLogs = 3600


# In[12]:


import sys, fcntl, time


# In[13]:


def stime():
    """Return current time as YYYY-MM-DD HH:MM:SS"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def appendToFile(filename, writestring):
    """Write-Append data; add linefeed"""

    with open(filename, 'at', encoding="UTF-8", errors='replace', buffering = 1) as f:
        f.write((writestring + "\n"))


# In[14]:




def decrypt(key,  data):
    cstate = [0x48,  0x74,  0x65,  0x6D,  0x70,  0x39,  0x39,  0x65]
    shuffle = [2, 4, 0, 7, 1, 6, 5, 3]
    
    phase1 = [0] * 8
    for i, o in enumerate(shuffle):
        phase1[o] = data[i]
    
    phase2 = [0] * 8
    for i in range(8):
        phase2[i] = phase1[i] ^ key[i]
    
    phase3 = [0] * 8
    for i in range(8):
        phase3[i] = ( (phase2[i] >> 3) | (phase2[ (i-1+8)%8 ] << 5) ) & 0xff
    
    ctmp = [0] * 8
    for i in range(8):
        ctmp[i] = ( (cstate[i] >> 4) | (cstate[i]<<4) ) & 0xff
    
    out = [0] * 8
    for i in range(8):
        out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff
    
    return out

def hd(d):
    return " ".join("%02X" % e for e in d)

if __name__ == "__main__":
    # Key retrieved from /dev/random, guaranteed to be random ;)
    key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]
    
    fp = open(sys.argv[1], "a+b",  0)
    #fp = open(deviceName, "a+b",  0)
    
    HIDIOCSFEATURE_9 = 0xC0094806
    set_report3 = b"\x00" + bytearray(key)
    fcntl.ioctl(fp, HIDIOCSFEATURE_9, set_report3)
    
    values = {}
    co2 = temp = humid = float('nan')
    lastTime = time.time()
    
    while True:
        #data = list(ord(e) for e in fp.read(8))
        bindata = fp.read(8)# No need for ord in Python 3? Values read are already ints
        data = list(bindata)
        
        decrypted = decrypt(key, data)
        if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
            print (hd(data), " => ", hd(decrypted),  "Checksum error")
        else:
            op = decrypted[0]
            val = decrypted[1] << 8 | decrypted[2]
            
            values[op] = val
            
            # Output all data, mark just received value with asterisk
            #print (", ".join( "%s%02X: %04X %5i" % ([" ", "*"][op==k], k, v, v) for (k, v) in sorted(values.items())), "  ", )
            ## From http://co2meters.com/Documentation/AppNotes/AN146-RAD-0401-serial-communication.pdf
#            if 0x50 in values:
#                print ("CO2: %4i" % values[0x50], )
#            if 0x42 in values:
#                print ("T: %2.2f" % (values[0x42]/16.0-273.15), )
#            if 0x44 in values:
#                print ("RH: %2.2f" % (values[0x44]/100.0), )
#            print

            if 0x50 in values:      co2   = values[0x50]
            if 0x42 in values:      temp  = values[0x42] / 16.0 - 273.15
            if 0x44 in values:      humid = values[0x44] / 100.0
                
            print("\t{:s} CO2: {:3.0f} ppm,  \tT: {:2.2f} °C".format(stime(), co2, temp))
            
            # Every secondsBetweenLogs seconds...
            if(time.time() > lastTime + secondsBetweenLogs):
                # Log to file
                lastTime = time.time()
                logstring = "{:s}, {:5.0f}, {:6.2f}".format(stime(), co2, temp)
                appendToFile(logFile, logstring)


# In[ ]:





# In[ ]:




