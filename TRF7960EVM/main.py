#!/usr/bin/python
'''
uvrfid
TRF7960EVM test
Copyright 2011 John McMaster <johnDMcMaster@gmail.com>
Licensed under the terms of the LGPL V3 or later, see COPYING for details

Think all responses are single line...will fixup after when I know for sure
Someone doesn't know how to spell "length" apparantly
	[mcmaster@gespenst sloc136_TRF7960_Firmware_Source_Code]$ fgrep -Hn 'lenght' *.c *.h |wc -l
	99
'''

'''
The mystical flags variable

'''

import sys 
import os.path
import select
import serial

VERSION = '0.1'

def to_hex(s):
	ret = ''
	for x in s:
		ret += '%02X' % ord(x) 	
	return ret

def from_hex_char(c):
	if not len(c) is 1:
		raise Exception('expected single char')
	c = c.upper()
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

Table 5-31
bit: description
7: command control bit
	0: address
	1: command
6: R/W
	R: 1
	W: 0
	Command: 0
5: Continuous address mode
	1: continuous
	Command: 0
4: Address / command bit 4
3: Address / command bit 3
2: Address / command bit 2
1: Address / command bit 1
0: Address / command bit 0

When writing more than 12 bits to FIFO, continuous address mode should be 1
'''
class RFID:
	device = "/dev/ttyUSB0"
	# file
	f = None
	
	def __init__(self):
		# set the termios, consider switching over to PySerial completly
		#ser = serial.Serial(self.device, 115200, timeout=1)
		#x = ser.read()          # read one byte
		#s = ser.read(10)        # read up to ten bytes (timeout)
		#line = ser.readline()   # read a '\n' terminated line
		#ser.close()

		self.f = open(self.device, "w+")
		# Try to flush old garbage
		#self.read_all()
	
	'''
	Utility
	'''
	
	'''
	Code seems to indicate second byte should be 0x08 when not checked (size of 0)
	'''
	
	def send(self, s):
		return self.send_hex(to_hex(s))
		
	def send_hex(self, s):
		'''
		All messages must begin with '01' and end with at least \n (\r is 
		pbuf = &buf[4];
			01 byte wasn't stored

		[-1]: magic byte (01)
			helps to re-sync protocol
			Index skipped in all other descriptions since its skipped in code
		[0]: arg0 (always data length?)
		[1]: arg1
		[2]: arg2
		[3]: arg2
		[4]: command
		[5...]: data (optional)
		
		Since first byte is inferred, all other seq notations will omit it
		'''
		
		s = s.upper()
		
		for c in s:
			if not (c >= 'A' and c <= 'F' or c >= '0' and c <= '9'):
				raise Exception('requires hex string') 
		
		to_write = '01%s\r\n' % s
		print 'to board: %s' % to_write.strip()
		self.f.write(to_write)
		self.f.flush()
		# Eat the response
		echoed = self.f.readline()

		# Mayhe should eat until its correct?
		# need to figure out how to poll though or might freeze up
		if to_write != echoed:
			print 'to write: %s' % to_write
			print 'echoed: %s' % echoed
			raise Exception('did not echo correctly')
	
	def send_simple_hex(self, c):
		'''Single command without any args'''
		self.send_hex('08000000%s' % c)

	def send_parts(self, args, command, payload):
		'''all as bytes'''
		if len(args) > 3:
			raise Exception("too many args")
		
		command_string = ''
		command_string += to_hex(args)
		command_string += filler_hex() * (4 - len(args))
		# [4]: command
		command_string += to_hex(command)
		command_string += to_hex(payload)

		return self.send_hex(command_string)

	def send_parts_raw(self, args, payload):
		'''all as bytes'''
		if len(args) > 3:
			raise Exception("too many args")
		
		command_string = ''
		command_string += to_hex(args)
		command_string += filler_hex() * (3 - len(args))
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
		
	def read_all(self):
		ret = ''
		while True:
			# Data ready?
			(rlist, wlist, xlist) = select.select([self.f], None, None, 0)
			if len(rlist) == 0:
				break
			ret += self.f.read()
		return ret
		
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
			data += chr(address)
			data += chr(byte)
		
		# two bytes per register + magic
		self.send_parts(chr(len(data) + 8), '\x10', data)
		# "Register write request."
		print self.f.readline().strip()

	def reg_write_continuous(self, base_address, bytes):
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
		data += ord(base_address)
		for byte in bytes:
			data += ord(byte)
		# one byte + register + base + magic
		self.send_parts(ord(len(data) + 1 + 8), '\x11', data)
		# "Continous write request."
		return self.f.readline().strip()
		
	def reg_read(self, address):
		'''Read from one and only one register, input as bytes'''
		return self.reg_read_single([address])

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
			data += '%c' % address
		
		# one bytes per register + magic
		self.send_parts(ord(len(targets) + 8), '\x12', data)
		# "Register read request.\r\n"
		print self.f.readline().strip()
		return self.read_response_bytes()

	def reg_read_continuous(self, base_address, count):
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
		data += '%c' % base_address
		data += '%c' % count
		self.send_parts('', '\x13', data)
		# ""Continous read request\r\n""
		print self.f.readline().strip()
		return self.read_response_bytes()

	def inventory(self, flags):
		'''
		0x14
		ISO 15693 Inventory request
		'''
		self.send_parts('', '\x14', chr(flags))
		# "ISO 15693 Inventory request.\r\n"
		print self.f.readline().strip()

	def write_raw(self, byte):
		'''Raw SPI/parallel line write (single byte as str)'''
		'''
		0x15
		direct command
		
		[5]: byte
		'''
		
		# Length is inferred
		self.send_parts('', '\x15', byte)
		# "RAW mode.\r\n"
		return self.f.readline().strip()

	def write_raw(self, bytes):
		'''Raw SPI/parallel line write (multi byte as str)'''
		'''
		0x16
		RAW mode
		
		[0]: data size + 8
		[5...]: data
		'''
		
		# length + magic (no register)
		self.send_parts(ord(len(bytes) + 8), '\x16', bytes)
		# "RAW mode.\r\n"
		return self.f.readline().strip()

	def request_mode(self, bytes):
		'''?'''
		'''
		0x18
		request code/mode
		Semantics are somewhat complicated and lacking comments, not sure what this does
		
		[0]: data size + 8
		[5...]: data
		'''
		
		# length + magic (no register)
		self.send_parts(ord(len(bytes) + 8), '\x18', bytes)
		# "Request mode.\r\n"
		return self.f.readline().strip()

	def change_bit_rate_core(self, bit_rate):
		'''change bit rate'''
		'''
		0x19
		testing 14443A - sending and recieving
		change bit rate
		
		[0]: data size + 9
		[5]: bit rate
		'''
		
		# length + magic (why 9 on this one?)
		self.send_parts(ord(len(bytes) + 9), '\x19', bit_rate)
		# "14443A Request - change bit rate.\r\n"
		return self.f.readline().strip()

	def TI_SID_poll(self, flags):
		'''Poll the SID (TI)'''
		'''
		0x34
		Ti SID poll
		
		[0]: data size + 8
		[5]: flags
		'''
		
		# length + magic
		self.send_parts(ord(len(bytes) + 9), '\x34', flags)
		# "Ti SID Poll.\r\n"
		print self.f.readline().strip()
		# At least sometimes returns something
		return self.read_response_bytes()

	def set_direct_mode(self):
		'''Put into direct mode'''
		'''
		0x0F
		Direct mode		
		'''
		
		# length + magic
		self.send_simple_hex('\x0F')
		# "Direct mode.\r\n"
		print self.f.readline().strip()

	def REQB(self, slots):
		'''Request A?'''
		'''
		0xB0
		14443B REQB
		Calls AnticollisionSequenceB(command, slots)
		
		[4]: command (0xB0)
		[5]: slots
		'''
		
		# length + magic
		self.send_parts('', '\xB0', slots)
		# "14443B REQB.\r\n"
		print self.f.readline().strip()

	def WUPB(self, slots):
		'''Wakeup B?'''
		'''
		0xB1
		WUPB
		Nearly identical to above
		
		[4]: command (0xB1)
		[5]: slots
		'''
		
		# length + magic
		self.send_parts('', '\xB1', slots)
		# "14443B REQB.\r\n"
		print self.f.readline().strip()

	def REQA(self, REQA_arg):
		'''Request A?'''
		'''
		0xA0 - REQA
		Calls AnticollisionSequenceA(REQA)
		
		[4]: command (0xA0)
		[5]: REQA for 
		'''
		
		# length + magic
		self.send_parts('', '\xA0', chr(REQA_arg))
		# "14443A REQA.\r\n"
		print self.f.readline().strip()
		# Do all of these have a response?  Skip for now

	def WUPB(self, WUPB_arg):
		'''Wakeup B?'''
		'''
		0xA1
		Guessing this is WUPB
		
		[4]: command (0xA0)
		[5]: REQA for 
		'''
		
		# length + magic
		self.send_parts('', '\xA1', WUPB_arg)
		# "14443A REQA.\r\n"
		print self.f.readline().strip()

	def disable_reader(self):
		# commented out for some reason in firmware source code
		# This could be re-implemented if desirable
		raise Exception('unsupported by firmware')

	def enable_reader(self):
		return self.set_mode('\xFF')

	def enable_reader(self):
		return self.set_mode('\xFF')

	def enable_reader(self):
		return self.set_mode('\xFF')

	def set_mode(self, mode):
		'''
		0xA2
		14443A Select
		'''
		# length + magic
		self.send_parts('', '\xA2', mode)
		'''
		One of (NOTE THE MISSING NEWLINE!):
			"Reader disabled."
			"External clock."
			"Internal clock."
		'''
		# Since we get no newline, just consume all
		self.read_all()

	'''
	0x03
	enable or disable the reader chip
	'''

	def set_AGC(self, use_AGC = True):
		'''Toggle automatic gain control (AGC)'''
		'''
		0xF0
		AGC toggle
		
		[4]: command (0xF0)
		[5]: 0xFF to turn on, turned off otherwise 
		'''
		
		if use_AGC:
			payload = '\x00'
		else:
			payload = '\xFF'
		
		# length + magic
		self.send_parts('', '\xF0', payload)
		# No response

	def set_modulation(self, use_PM):
		'''Set modulation scheme'''
		'''
		0xF1
		One of:
			amplitude modulation (AM)
			phase modulation (PM)
		
		[4]: command (0xF0)
		[5]: 0xFF to turn on, turned off otherwise 
		'''
		
		if use_PM:
			payload = '\x00'
		else:
			payload = '\xFF'
		
		# length + magic
		self.send_parts('', '\xF1', payload)
		# No response

	def set_full_power(self, use_FP = True):
		'''Set power level'''
		'''
		0xF2
		Full - half power selection (FF - full power)
		
		[4]: command (0xF0)
		[5]: 0xFF to turn on, turned off otherwise 
		'''
		
		if use_FP:
			payload = '\xFF'
		else:
			payload = '\x00'
		
		# length + magic
		self.send_parts('', '\xF2', payload)
		# No response

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

	'''
	Composite commands
	'''
	
	def set_14443A_half_power(self):
		'''
		0031
			write reg
			reg: 00
				chip status control
			value: 31
				20: RF output active
				10: half output power
				1: 5 V operation
		0109
			write reg
			reg: 01
				IS control
			value: 09
				RFID mode = ISO14443A high bit rate 212 kbps
		'''
		self.reg_write_single([(0x00, 0x31), (0x01, 0x09)])

	def set_14443A_full_power(self):
		'''
		0021
			write reg
			reg: 00
				chip status control
			value: 21
				20: RF output active
				1: 5 V operation
		0109
			write reg
			reg: 01
				IS control
			value: 09
				RFID mode = ISO14443A high bit rate 212 kbps
		'''
		self.reg_write_single([(0x00, 0x21), (0x01, 0x09)])

	def anticollision(self):
		self.REQA(0x01)
		'''
		No card
			()
		With card
			(0123)(...
			Long line
		'''
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

	rfid.set_14443A_full_power()
	rfid.inventory(0xFF)
	res = rfid.anticollision()
	print res

	
	while True:
		print rfid.f.readline().strip()
	
	print 'Done!'

