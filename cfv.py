#! /usr/bin/env python

#    cfv - Command-line File Verify
#    Copyright (C) 2000-2009  Matthew Mueller <donut AT dakotacom DOT net>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import os, sys, struct
from stat import *

stdprogress = None

try:
	if os.environ.get('CFV_NOMMAP'): raise ImportError
	# mmap is broken in python 2.4.2 and leaks file descriptors
	if sys.version_info[:3] == (2, 4, 2): raise ImportError
	import mmap
	if hasattr(mmap, 'ACCESS_READ'):
		def dommap(fileno, len):#generic mmap.  python2.2 adds ACCESS_* args that work on both nix and win.
			if len==0: return '' #mmap doesn't like length=0
			return mmap.mmap(fileno, len, access=mmap.ACCESS_READ)
	elif hasattr(mmap, 'PROT_READ'):
		def dommap(fileno, len):#unix mmap.  python default is PROT_READ|PROT_WRITE, but we open readonly.
			if len==0: return '' #mmap doesn't like length=0
			return mmap.mmap(fileno, len, mmap.MAP_SHARED, mmap.PROT_READ)
	else:
		def dommap(fileno, len):#windows mmap.
			if len==0: return ''
			return mmap.mmap(fileno, len)
	nommap=0
except ImportError:
	nommap=1

_MAX_MMAP = 2**32 - 1
_FALLBACK_MMAP = 2**31 - 1
def _getfilechecksum(file, hasher):
	f=open(file,'rb')
	def finish(m,s,f=f,file=file):
		if stdprogress: progress.init(file)
		try:
			while 1:
				x=f.read(65536)
				if not x:
					return m.digest(),s
				s=s+len(x)
				m.update(x)
				if stdprogress: progress.update(s)
		finally:
			if stdprogress: progress.cleanup()

	if f==sys.stdin or nommap or stdprogress:
		return finish(hasher(),0L)
	else:
		s = os.path.getsize(file)
		try:
			if s > _MAX_MMAP:
				# Work around python 2.[56] problem with md5 of large mmap objects
				raise OverflowError
			m = hasher(dommap(f.fileno(), s))
		except OverflowError:
			mmapsize = min(s, _FALLBACK_MMAP) #mmap size is limited by C's int type, which even on 64 bit arches is often 32 bits, so we can't use sys.maxint either.  If we get the error, just assume 32 bits. 
			m = hasher(dommap(f.fileno(), mmapsize))
			f.seek(mmapsize)
			return finish(m,mmapsize) #unfortunatly, python's mmap module doesn't support the offset parameter, so we just have to do the rest of the file the old fashioned way.
		return m.digest(),s
			
try:
	import zlib
	_crc32=zlib.crc32
except ImportError:
	import binascii
	_crc32=binascii.crc32
class CRC32:
	digest_size = 4
	def __init__(self, s=''):
		self.value = _crc32(s)
	def update(self, s):
		self.value = _crc32(s, self.value)
	def digest(self):
		return struct.pack('>I', self.value & 0xFFFFFFFF)

def getfilecrc(file):
	return _getfilechecksum(file, CRC32)


