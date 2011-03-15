#!/usr/bin/python
'''
uvrfid
TRF7960EVM test
Copyright 2011 John McMaster <johnDMcMaster@gmail.com>
Licensed under the terms of the LGPL V3 or later, see COPYING for details
'''

import sys 
import os.path

VERSION = '0.1'

'''
Protocol
All written bytes are echoed
2 leading bytes
	the character 0 followed by 1
4 data bytes
	represented by 8 ASCII hex chars
1 command byte
Newline termination
	\n
'''
class RFID:
	device = "/dev/ttyUSB0"
	# file
	f = None
	
	def __init__(self):
		self.f = open(self.device, "w+")
	
	'''
	0x10
	register write (adress:data, adress:data
	'''

	'''
	0x11
	continous write (adress:data, data, ...)
	'''

	'''
	0x12
	register read (adress:data, adress:data, ...)
	'''

	'''
	0x13
	continous read (adress:data, data, ...)
	'''

	'''
	0x14
	ISO 15693 Inventory request
	'''

	'''
	0x15
	direct command
	'''

	'''
	0x16
	RAW mode
	'''

	'''
	0x18
	request code/mode
	'''

	'''
	0x19
	testing 14443A - sending and recieving
	change bit rate
	'''

	'''
	0x34
	Ti SID poll
	'''

	'''
	0x0F
	Direct mode
	'''

	'''
	0xB0
	REQB
	14443B REQB
	'''

	'''
	0xB1
	WUPB
	'''

	'''
	0xA0 - REQA
	0xA1
	'''

	'''
	0xA2
	14443A Select
	'''

	'''
	0x03
	enable or disable the reader chip
	'''

	'''
	0xF0
	AGC toggle
	'''

	'''
	0xF1
	AM PM toggle
	'''

	'''
	0xF2
	Full - half power selection (FF - full power)
	'''

	def get_version(self):
		'''
		phello = "Firmware Version 3.2.EXP.NOBB \r\n";
		
		01FEFEFEFEFE
		Firmware Version 3.2.EXP.NOBB
		
		Also it echos back, so we need to discard the echo (or verify...)
		'''
		self.f.write('0100000000FE\r\n')
		self.f.flush()
		echoed = self.f.readline()
		ret = self.f.readline()
		ret = ret.strip()
		
		return ret

	def get_info(self):
		'''
		phello = "TRF7960 EVM \r\n";
		'''
		self.f.write('0100000000FF\r\n')
		self.f.flush()
		echoed = self.f.readline()
		ret = self.f.readline()
		ret = ret.strip()
		
		return ret

def help():
	print 'uvrfid version %s' % VERSION
	print 'Copyright 2011 John McMaster <JohnDMcMaster@gmail.com>'
	print 'Usage:'
	print 'uvrfid [args]'

def arg_fatal(s):
	print s
	help()
	sys.exit(1)


if __name__ == "__main__":
	image_file_names = list()
	project_file_names = list()
	
	for arg_index in range (1, len(sys.argv)):
		arg = sys.argv[arg_index]
		arg_key = None
		arg_value = None
		if arg.find("--") == 0:
			arg_value_bool = True
			if arg.find("=") > 0:
				arg_key = arg.split("=")[0][2:]
				arg_value = arg.split("=")[1]
				if arg_value == "false" or arg_value == "0" or arg_value == "no":
					arg_value_bool = False
			else:
				arg_key = arg[2:]

			if arg_key == "help":
				help()
				sys.exit(0)
			else:
				arg_fatal('Unrecognized arg: %s' % arg)
		else:
			if False:
				pass
			else:
				arg_fatal('unrecognized arg: %s' % arg)

	rfid = RFID()
	print 'version: %s' % rfid.get_version()
	print 'info: %s' % rfid.get_info()
	
	print 'Done!'

