#!/usr/bin/python
'''
uvrfid
TRF7960EVM test
Copyright 2011 John McMaster <johnDMcMaster@gmail.com>
Licensed under the terms of the LGPL V3 or later, see COPYING for details

Think all responses are single line...will fixup after when I know for sure
'''

import sys 
import os.path

VERSION = '0.1'

def to_hex(s):
	ret = ''
	for x in s:
		ret += '%02X' % x 	
	return ret

def from_hex_char(c):
	if not len(c) is 1:
		raise Exception('expected single char')
	c = c.uppercase()
	if c >= '0' and c <= '9':
		return ord(c - '0')
	elif c >= 'A' and c <= 'F':
		return ord(c - 'A') + 10
	else:
		raise Exception('expected hex char')

def from_hex(s):
	ret = ''
	if not len(s) % 2 == 0:
		raise Exception('input must be even')
	for i in range(0, len(s), 2):
		ret += chr(from_hex_char(s[i]) << 8) + from_hex_char(s[i + 1])
	return ret

def filler_hex():
	return '00'

def filler_byte():
	return '\x00'

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
	Utility
	'''
	
	def send(self, s):
		return self.send_hex(to_hex(s))
		
	def send_hex(self, s):
		'''
		All messages must begin with '01' and end with at least \n (\r is 
		pbuf = &buf[4];
			01 byte wasn't stored

		[0]: magic byte (01)
			helps to re-sync protocol
		[1]: arg0 (always data length?)
		[2]: arg1
		[3]: arg2
		[4]: command
		[5...]: data (optional)
		
		Since first byte is inferred, all other seq notations will omit it
		'''
		
		s = s.uppercase()
		
		for c in s:
			if not (c >= 'A' and c <= 'F' or c >= '0' and c <= '9'):
				raise Exception('requires hex string') 
		
		to_write = '01%s\r\n' % s
		self.f.write(to_write)
		self.f.flush()
		# Eat the response
		echoed = self.f.readline()

		# Mayhe should eat until its correct?
		# need to figure out how to poll though or might freeze up
		if to_write != echoed:
			raise Exception('did not echo correctly')
	
	def send_simple_hex(self, c):
		'''Single command without any args'''
		self.send_hex('00000000%s\r\n', c)

	def send_parts(self, args, command, payload):
		'''all as bytes'''
		if len(args) > 3:
			raise Exception("too many args")
		
		command_string = ''
		command_string += to_hex(args)
		command_string += filler_hex() * (3 - len(args))
		# [3]: command
		command_string += to_hex(command)
		command_string += to_hex(payload)

		return self.send_hex(command_string)

	def read_response_bytes(self):
		'''Parse response binary'''
		'''
		Should be of form "[012345]\r\n"
		'''
		line = f.readline().strip()
		if len(line) < 2 or (not line[0] == '[') or (not line[-1] == ']'):
			raise Exception("malformed response")
		
		line = line[1:-1]
		
	'''
	Commands
	'''

	'''
	Register address space
	All regs are byte
     Adr (hex)     Register                                      Read/Write
	Main Control Registers
	 00           Chip status control                            R/W
	 01           ISO control                                    R/W
	Protocol Sub-Setting Registers
	 02           ISO14443B TX options                           R/W
	 03           ISO 14443A high bit rate options               R/W
	 04           TX timer setting, H-byte                       R/W
	 05           TX timer setting, L-byte                       R/W
	 06           TX pulse-length control                        R/W
	 07           RX no response wait                            R/W
	 08           RX wait time                                   R/W
	 09           Modulator and SYS_CLK control                  R/W
	 0A           RX special setting                             R/W
	 0B           Regulator and I/O control                      R/W
	 16           Unused                                         NA
	 17           Unused                                         NA
	 18           Unused                                         NA
	 19           Unused                                         NA
	Status Registers
	 0C           IRQ status                                     R
	 0D           Collision position and interrupt mask register R/W
	 0E           Collision position                             R
	 0F           RSSI levels and oscillator status              R
	FIFO Registers
	 1C           FIFO status                                    R
	 1D           TX length byte1                                R/W
	 1E           TX length byte2                                R/W
	 1F           FIFO I/O register                              R/W
	
	'''
	def reg_write(self, address, byte):
		'''Write to one and only one register, input as bytes'''
		return self.reg_write_single((address, byte))

	def reg_write_single(self, targets):
		'''Write to an array of registers, input as (address, byte) as bytes'''
		'''
		0x10
		register write (adress:data, adress:data
		
		[0]: data size + 8
			How odd...
			Must be some shift register thing
		[5]: register (masked 0x1f)
		[6...]: data
		'''
		data = ''
		
		for (address, byte) in targets:
			# First byte is address
			data += to_hex(address)
			data += to_hex(byte)
		
		# two bytes per register + magic
		self.send_parts(len(data) + 8, '\x10', data)				
		# "Register write request."
		return self.f.readline().strip()

	def reg_write_continuous(self, base_address, bytes)
		'''Write to a series of registers given base and incrementing, input as bytes'''
		'''
		0x11
		continous write (adress:data, data, ...)
		
		[0]: data size + 8
			How odd...
			Must be some shift register thing
		[5]: register (masked 0x1f)
		[6...]: data
		'''
		data = ''
		data += to_hex(base_address)
		for byte in bytes:
			data += to_hex(byte)
		# one byte + register + base + magic
		self.send_parts(len(data) + 1 + 8, '\x11', data)				
		# "Continous write request."
		return self.f.readline().strip()
		
	def reg_read(self, address, byte):
		'''Read from one and only one register, input as bytes'''
		return self.reg_read_single([address[)

	def reg_read_single(self, addresses):
		'''Read from an array of registers, input as (address) as bytes'''
		'''
		0x12
		register read (adress:data, adress:data, ...)
		
		[0]: data size + 8
		[5 + i]: register (masked 0x1f)
		'''
		data = ''
		
		for address in addresses:
			# First byte is address
			data += to_hex(address)
		
		# one bytes per register + magic
		self.send_parts(len(targets) + 8, '\x12', data)				
		# "Register read request.\r\n"
		self.f.readline().strip()
		return self.read_response_bytes()

	def reg_read_continuous(self, base_address)
		'''Read from a series of registers given base and incrementing, input as bytes'''
		'''
		0x13
		continous read (adress:data, data, ...)
		
		[0]: data size + 8
			How odd...
			Must be some shift register thing
		[5]: start register (masked 0x1f)
		'''
		data = ''
		data += to_hex(base_address)
		# one byte + register + base + magic
		self.send_parts(len(data) + 1 + 8, '\x13', data)
		# ""Continous read request\r\n""
		self.f.readline().strip()
		return self.read_response_bytes()

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
		self.send_simple_hex('FE')
		return self.f.readline().strip()

	def get_info(self):
		'''
		phello = "TRF7960 EVM \r\n";
		'''
		self.send_simple_hex('FF')
		return self.f.readline().strip()

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

