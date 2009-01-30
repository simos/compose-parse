#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# compose-parse.py, version 1.3
#
# multifunction script that helps manage the compose sequence table in GTK+ (gtk/gtkimcontextsimple.c)
# the script produces statistics and information about the whole process, run with --help for more.
#
# You may need to switch your python installation to utf-8, if you get 'ascii' codec errors.
#
# Complain to Simos Xenitellis (simos@gnome.org, http://simos.info/blog) for this craft.

from re			import findall, match, split, sub
from string		import atoi
from unicodedata	import normalize, decimal
from urllib 		import urlretrieve
from os.path		import isfile, getsize
from copy 		import copy

import sys
import getopt

# We grab files off the web, left and right.
URL_COMPOSE = 'http://gitweb.freedesktop.org/?p=xorg/lib/libX11.git;a=blob_plain;f=nls/en_US.UTF-8/Compose.pre'
URL_KEYSYMSTXT = 'http://www.cl.cam.ac.uk/~mgk25/ucs/keysyms.txt'
URL_GDKKEYSYMSH = 'http://svn.gnome.org/svn/gtk%2B/trunk/gdk/gdkkeysyms.h'
URL_UNICODEDATATXT = 'http://www.unicode.org/Public/5.0.0/ucd/UnicodeData.txt'
URL_GTKOLDSEQUENCES = 'http://simos.info/pub/GTKOLDSEQUENCES.txt'
FILENAME_COMPOSE_LOOKASIDE = 'gtk-compose-lookaside.txt'
FILENAME_COMPOSE_WIN32 = 'gtk-win32-sequences.txt'

# We currently support keysyms of size 2; once upstream xorg gets sorted, 
# we might produce some tables with size 2 and some with size 4.
SIZEOFINT = 2

# Current max compose sequence length; in case it gets increased.
WIDTHOFCOMPOSETABLE = 5

keysymdatabase = {}
keysymunicodedatabase = {}
unicodedatabase = {}
gtkoldsequences = {}
multisequences = {}
multisequence_maxseqlen = 0
multisequence_maxvallen = 0

headerfile_start = """/* GTK - The GIMP Tool Kit
 * Copyright (C) 2007, 2008, 2009 GNOME Foundation
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

/*
 * File auto-generated from script found at http://bugzilla.gnome.org/show_bug.cgi?id=321896
 * using the input files
 *  Input   : http://gitweb.freedesktop.org/?p=xorg/lib/libX11.git;a=blob_plain;f=nls/en_US.UTF-8/Compose.pre
 *  Input   : http://www.cl.cam.ac.uk/~mgk25/ucs/keysyms.txt
 *  Input   : http://www.unicode.org/Public/UNIDATA/UnicodeData.txt
 *
 * This table is optimised for space and requires special handling to access the content.
 * This table is used solely by http://svn.gnome.org/viewcvs/gtk%2B/trunk/gtk/gtkimcontextsimple.c
 * 
 * The resulting file is placed at http://svn.gnome.org/viewcvs/gtk%2B/trunk/gtk/gtkimcontextsimpleseqs.h
 * This file is described in bug report http://bugzilla.gnome.org/show_bug.cgi?id=321896
 */

/*
 * Modified by the GTK+ Team and others 2007, 2008, 2009.  See the AUTHORS
 * file for a list of people on the GTK+ Team.  See the ChangeLog
 * files for a list of changes.  These files are distributed with
 * GTK+ at ftp://ftp.gtk.org/pub/gtk/.
 */

#ifndef __GTK_IM_CONTEXT_SIMPLE_SEQS_H__
#define __GTK_IM_CONTEXT_SIMPLE_SEQS_H__

/* === These are the original comments of the file; we keep for historical purposes ===
 *
 * The following table was generated from the X compose tables include with
 * XFree86 4.0 using a set of Perl scripts. Contact Owen Taylor <otaylor@redhat.com>
 * to obtain the relevant perl scripts.
 *
 * The following compose letter letter sequences confliced
 *   Dstroke/dstroke and ETH/eth; resolved to Dstroke (Croation, Vietnamese, Lappish), over
 *                                ETH (Icelandic, Faroese, old English, IPA)  [ D- -D d- -d ]
 *   Amacron/amacron and ordfeminine; resolved to ordfeminine                 [ _A A_ a_ _a ]
 *   Amacron/amacron and Atilde/atilde; resolved to atilde                    [ -A A- a- -a ]
 *   Omacron/Omacron and masculine; resolved to masculine                     [ _O O_ o_ _o ]
 *   Omacron/omacron and Otilde/atilde; resolved to otilde                    [ -O O- o- -o ]
 *
 * [ Amacron and Omacron are in Latin-4 (Baltic). ordfeminine and masculine are used for
 *   spanish. atilde and otilde are used at least for Portuguese ]
 *
 *   at and Aring; resolved to Aring                                          [ AA ]
 *   guillemotleft and caron; resolved to guillemotleft                       [ << ]
 *   ogonek and cedilla; resolved to cedilla                                  [ ,, ]
 *
 * This probably should be resolved by first checking an additional set of compose tables
 * that depend on the locale or selected input method.
 */

static const guint16 gtk_compose_seqs_compact[] = {"""

headerfile_end = """};

#endif /* __GTK_IM_CONTEXT_SIMPLE_SEQS_H__ */
"""

multipleseqs_file_start = """/* GTK - The GIMP Tool Kit
 * Copyright (C) 2007, 2008, 2009 GNOME Foundation
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

/* This file is gtkimcontextsimplemultiseqs.h.
 * This table is for compose sequences that produce two or more characters.
 * These sequences where extracted from the upstream Compose file from X.Org.
 * This file was generated with http://svn.gnome.org/svn/gtk+/trunk/gtk/compose-parse.py
 *
 * The table is composed of two parts, $compose_max_sequence_len columns for
 * the sequence, and $compose_max_codepoint_len columns for the printed character.
 * We pad with 0 for any missing keys or characters.
 * The number of sequences is $compose_multi_index_size.
 */
"""

multipleseqs_file_middle = """
static const guint16 gtk_compose_seqs_multi[] = {"""

multipleseqs_file_end = """};
"""



win32seqs_file_start = """/* GTK - The GIMP Tool Kit
 * Copyright (C) 2007, 2008, 2009 GNOME Foundation
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

/* This file is gtkimcontextsimplewin32seqs.h.
 * This table is for compose sequences to be used on Win32 systems.
 * These sequences where extracted from the file gtk-win32-sequences.txt
 * This file was generated with http://svn.gnome.org/svn/gtk+/trunk/gtk/compose-parse.py
 */
"""

win32seqs_file_middle = """static const guint16 gtk_compose_seqs_win32[] = {"""

win32seqs_file_end = """};
"""



def stringtohex(str): return atoi(str, 16)

def factorial(n): 
	if n <= 1:
		return 1
	else:
		return n * factorial(n-1)

def uniq(*args) :
	""" Performs a uniq operation on a list or lists """
    	theInputList = []
    	for theList in args:
    	   theInputList += theList
    	theFinalList = []
    	for elem in theInputList:
		if elem not in theFinalList:
          		theFinalList.append(elem)
    	return theFinalList



def all_permutations(seq):
	""" Borrowed from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/252178 """
	""" Produces all permutations of the items of a list """
    	if len(seq) <=1:
    	    yield seq
    	else:
    	    for perm in all_permutations(seq[1:]):
    	        for i in range(len(perm)+1):
    	            #nb str[0:1] works in both string and list contexts
        	        yield perm[:i] + seq[0:1] + perm[i:]

def usage():
	print """compose-parse available parameters:
	-a, --algorithmic	show sequences saved with algorithmic optimisation
	-e, --gtk-expanded	when used with --gtk, create file that repeats first column; not usable in GTK+
	-g, --gtk		show entries that go to GTK+
	-h, --help		this craft
        -m, --multiple		shows compose sequences that result to >1 unicode characters
	-n, --numeric		when used with --gtk, create file with numeric values only
        -p, --plane1		show plane1 compose sequences
	-q, --quiet   	 	do not show verbose output (default is verbose)
        -r, --regression	shows compose sequences that used to exist in pre-update, but are not found in Xorg's Compose.
	-s, --statistics	show overall statistics (both algorithmic, non-algorithmic)
	-u, --unicodedatatxt	show compose sequences derived from UnicodeData.txt (from unicode.org)
	-w, --warnings		show some non-fatal warnings (useful for maintainer)
            --win32             process gtk-win32-sequences.txt and produce gtkimcontextsimplewin32seqs.h

	Default is to show statistics.
	"""

try: 
	opts, args = getopt.getopt(sys.argv[1:], "aeghmnpqrsuw", 
		[ "algorithmic", "gtk-expanded", "gtk", "help", "multiple",
		  "numeric", "plane1", "quiet", "regression", 
		  "stats", "statistics", "unicodedatatxt", "warnings", "win32"])
except: 
	usage()
	sys.exit(2)

opt_algorithmic = False
opt_gtkexpanded = False
opt_gtk = False
opt_multiple = False
opt_numeric = False
opt_plane1 = False
opt_quiet = False
opt_regression = False
opt_statistics = False
opt_unicodedatatxt = False
opt_warnings = False
opt_win32 = False

no_options = True

for o, a in opts:
	if o in ("-a", "--algorithmic"):
		opt_algorithmic = True
		no_options = False
	if o in ("-e", "--gtk-expanded"):
		opt_gtkexpanded = True
		no_options = False
	if o in ("-g", "--gtk"):
		opt_gtk = True
		no_options = False
	if o in ("-h", "--help"):
		usage()
		sys.exit()
	if o in ("-m", "--multiple"):
		opt_multiple = True
		no_options = False
	if o in ("-n", "--numeric"):
		opt_numeric = True
		no_options = False
	if o in ("-p", "--plane1"):
		opt_plane1 = True
		no_options = False
	if o in ("-q", "--quiet"):
		opt_quiet = True
		no_options = False
	if o in ("-r", "--regression"):
		opt_regression = True
		no_options = False
	if o in ("-s", "--statistics"):
		opt_statistics = True
	if o in ("-u", "--unicodedatatxt"):
		opt_unicodedatatxt = True
		no_options = False
	if o in ("-w", "--warnings"):
		opt_warnings = True
	if o in ("--win32"):
		opt_win32 = True
		no_options = False

if no_options:
	opt_statistics = True

def download_hook(blocks_transferred, block_size, file_size):
	""" A download hook to provide some feedback when downloading """
	if blocks_transferred == 0:
		if file_size > 0:
			if not opt_quiet:
				print "Downloading", file_size, "bytes: ",
		else:	
			if not opt_quiet:
				print "Downloading: ",
	sys.stdout.write('#')
	sys.stdout.flush()


def download_file(url):
	""" Downloads a file provided a URL. Returns the filename. """
	""" Borks on failure """
	localfilename = url.split('/')[-1]
        if not isfile(localfilename) or getsize(localfilename) <= 0:
		if not opt_quiet:
			print "Downloading ", url, "..."
		try: 
			urlretrieve(url, localfilename, download_hook)
		except IOError, (errno, strerror):
			print "I/O error(%s): %s" % (errno, strerror)
			sys.exit(-1)
		except:
			print "Unexpected error: ", sys.exc_info()[0]
			sys.exit(-1)
		print " done."
        else:
		if not opt_quiet:
                	print "Using cached file for ", url
	return localfilename

def process_gdkkeysymsh():
	""" Opens the gdkkeysyms.h file from GTK+/gdk/gdkkeysyms.h """
	""" Fills up keysymdb with contents """
	filename_gdkkeysymsh = download_file(URL_GDKKEYSYMSH)
	try: 
		gdkkeysymsh = open(filename_gdkkeysymsh, 'r')
	except IOError, (errno, strerror):
		print "I/O error(%s): %s" % (errno, strerror)
		sys.exit(-1)
	except:
		print "Unexpected error: ", sys.exc_info()[0]
		sys.exit(-1)

	""" Parse the gdkkeysyms.h file and place contents in  keysymdb """
	linenum_gdkkeysymsh = 0
	keysymdb = {}
	for line in gdkkeysymsh.readlines():
		linenum_gdkkeysymsh += 1
		line = line.strip()
		if line == "" or not match('^#define GDK_', line):
			continue
		components = split('\s+', line)
		if len(components) < 3:
			print "Invalid line %(linenum)d in %(filename)s: %(line)s"\
			% {'linenum': linenum_gdkkeysymsh, 'filename': filename_gdkkeysymsh, 'line': line}
			print "Was expecting 3 items in the line"
			sys.exit(-1)
		if not match('^GDK_', components[1]):
			print "Invalid line %(linenum)d in %(filename)s: %(line)s"\
			% {'linenum': linenum_gdkkeysymsh, 'filename': filename_gdkkeysymsh, 'line': line}
			print "Was expecting a keysym starting with GDK_"
			sys.exit(-1)
		if components[2][:2] == '0x' and match('[0-9a-fA-F]+$', components[2][2:]):
			unival = atoi(components[2][2:], 16)
			if unival == 0:
				continue
			keysymdb[components[1][4:]] = unival
		else:
			print "Invalid line %(linenum)d in %(filename)s: %(line)s"\
			% {'linenum': linenum_gdkkeysymsh, 'filename': filename_gdkkeysymsh, 'line': line}
			print "Was expecting a hexadecimal number at the end of the line"
			sys.exit(-1)
	gdkkeysymsh.close()

	""" Patch up the keysymdb with some of our own stuff """

	""" This is for a missing keysym from the currently upstream file """
	#keysymdb['dead_stroke'] = 0x338

	""" This is for a missing keysym from the currently upstream file """
	keysymdb['dead_belowdiaeresis'] = 0x324
	keysymdb['dead_belowring'] 	= 0x325
	keysymdb['dead_belowcomma'] 	= 0x326
	keysymdb['dead_belowcircumflex']= 0x32d
	keysymdb['dead_belowbreve'] 	= 0x32e
	keysymdb['dead_belowtilde'] 	= 0x330
	keysymdb['dead_belowmacron'] 	= 0x331
	"""
	keysymdb['KP_Multiply']   	= 0x02a
	keysymdb['KP_Add']        	= 0x02b
	keysymdb['KP_Separator']  	= 0x02c
	keysymdb['KP_Subtract']   	= 0x02d
	keysymdb['KP_Decimal']    	= 0x02e
	keysymdb['KP_Divide']     	= 0x02f
	keysymdb['KP_0']          	= 0x030
	keysymdb['KP_1']          	= 0x031
	keysymdb['KP_2']          	= 0x032
	keysymdb['KP_3']          	= 0x033
	keysymdb['KP_4']          	= 0x034
	keysymdb['KP_5']          	= 0x035
	keysymdb['KP_6']          	= 0x036
	keysymdb['KP_7']          	= 0x037
	keysymdb['KP_8']          	= 0x038
	keysymdb['KP_9']          	= 0x039
	keysymdb['KP_Equal']      	= 0x03d
	"""
	""" This is^Wwas preferential treatment for Greek """
	# keysymdb['dead_tilde'] = 0x342  		
	""" This is^was preferential treatment for Greek """
	#keysymdb['combining_tilde'] = 0x342	

	""" Fixing VoidSymbol """
	keysymdb['VoidSymbol'] = 0xFFFF

	return keysymdb

def process_keysymstxt():
	""" Grabs and opens the keysyms.txt file that Markus Kuhn maintains """
	""" This file keeps a record between keysyms <-> unicode chars """
	filename_keysymstxt = download_file(URL_KEYSYMSTXT)
	try: 
		keysymstxt = open(filename_keysymstxt, 'r')
	except IOError, (errno, strerror):
		print "I/O error(%s): %s" % (errno, strerror)
		sys.exit(-1)
	except:
		print "Unexpected error: ", sys.exc_info()[0]
		sys.exit(-1)

	""" Parse the keysyms.txt file and place content in  keysymdb """
	linenum_keysymstxt = 0
	keysymdb = {}
	for line in keysymstxt.readlines():
		linenum_keysymstxt += 1
		line = line.strip()
		if line == "" or match('^#', line):
			continue
		components = split('\s+', line)
		if len(components) < 5:
			print "Invalid line %(linenum)d in %(filename)s: %(line)s'"\
			% {'linenum': linenum_keysymstxt, 'filename': filename_keysymstxt, 'line': line}
			print "Was expecting 5 items in the line"
			sys.exit(-1)
		if components[1][0] == 'U' and match('[0-9a-fA-F]+$', components[1][1:]):
			unival = atoi(components[1][1:], 16)
		if unival == 0:
			continue
		keysymdb[components[4]] = unival
	keysymstxt.close()

	""" Patch up the keysymdb with some of our own stuff """
	""" This is for a missing keysym from the currently upstream file """
	keysymdb['dead_belowdiaeresis'] = 0x324
	keysymdb['dead_belowring'] 	= 0x325
	keysymdb['dead_belowcomma'] 	= 0x326
	keysymdb['dead_belowcircumflex']= 0x32d
	keysymdb['dead_belowbreve'] 	= 0x32e
	keysymdb['dead_belowtilde'] 	= 0x330
	keysymdb['dead_belowmacron'] 	= 0x331
	"""
	keysymdb['KP_Multiply']   	= 0x02a
	keysymdb['KP_Add']        	= 0x02b
	keysymdb['KP_Separator']  	= 0x02c
	keysymdb['KP_Subtract']   	= 0x02d
	keysymdb['KP_Decimal']    	= 0x02e
	keysymdb['KP_Divide']     	= 0x02f
	keysymdb['KP_0']          	= 0x030
	keysymdb['KP_1']          	= 0x031
	keysymdb['KP_2']          	= 0x032
	keysymdb['KP_3']          	= 0x033
	keysymdb['KP_4']          	= 0x034
	keysymdb['KP_5']          	= 0x035
	keysymdb['KP_6']          	= 0x036
	keysymdb['KP_7']          	= 0x037
	keysymdb['KP_8']          	= 0x038
	keysymdb['KP_9']          	= 0x039
	keysymdb['KP_Equal']      	= 0x03d
	"""
	""" This is preferential treatment for Greek """
	""" => we get more savings if used for Greek """
	# keysymdb['dead_tilde'] = 0x342  		
	""" This is preferential treatment for Greek """
	# keysymdb['combining_tilde'] = 0x342	

	keysymdb['zerosubscript'] 	= 0x2080
	keysymdb['onesubscript'] 	= 0x2081
	keysymdb['twosubscript'] 	= 0x2082
	keysymdb['threesubscript'] 	= 0x2083
	keysymdb['foursubscript'] 	= 0x2084
	keysymdb['fivesubscript'] 	= 0x2085
	keysymdb['sixsubscript'] 	= 0x2086
	keysymdb['sevensubscript'] 	= 0x2087
	keysymdb['eightsubscript'] 	= 0x2088
	keysymdb['ninesubscript'] 	= 0x2089

	""" This is for a missing keysym from Markus Kuhn's db """
	keysymdb['dead_stroke'] = 0xFE63
	""" This is for a missing keysym from Markus Kuhn's db """
	keysymdb['Oslash'] = 0x0d8		

	""" This is for a missing (recently added) keysym """
	keysymdb['dead_psili'] = 0x313		
	""" This is for a missing (recently added) keysym """
	keysymdb['dead_dasia'] = 0x314		

	""" Allows to import Multi_key sequences """
	keysymdb['Multi_key'] = 0xff20

	""" New keysym (no corresponding Unicode character) """
	#keysymdb['dead_currency'] = 0xfe6f

	return keysymdb

def process_gtkoldsequences():
	""" Grabs and opens the keysyms.txt file that Markus Kuhn maintains """
	""" This file keeps a record between keysyms <-> unicode chars """
	filename_gtkoldsequences = download_file(URL_GTKOLDSEQUENCES)
	try: 
		gtkoldsequencestxt = open(filename_gtkoldsequences, 'r')
	except IOError, (errno, strerror):
		print "I/O error(%s): %s" % (errno, strerror)
		sys.exit(-1)
	except:
		print "Unexpected error: ", sys.exc_info()[0]
		sys.exit(-1)

	""" Parse the gtkoldsequences.txt file and place content in gtkoldsequences """
	linenum = 0
	for line in gtkoldsequencestxt.readlines():
		line = line.strip()
		components = split('\s+', line)
		if len(components) < 6:
			print "Invalid line in %(filename)s: %(line)s'"\
			% {'line': line, 'filename': filename_keysymstxt }
			print "Was expecting 6 items in the line"
			sys.exit(-1)
		components[5] = atoi(components[5], 16)
		sequence = components[0:6]
		sequence.append(False)
		if not gtkoldsequences.has_key(components[5]):
			gtkoldsequences[components[5]] = []
		gtkoldsequences[components[5]].append(sequence)
	gtkoldsequencestxt.close()
	return gtkoldsequences

def keysymvalue(keysym, file = "n/a", linenum = 0):
	""" Extracts a value from the keysym """
	""" Find the value of keysym, using the data from keysyms """
	""" Use file and linenum to when reporting errors """
	if keysym == "":
		return 0
       	if keysymdatabase.has_key(keysym):
               	return keysymdatabase[keysym]
       	elif keysym[0] == 'U' and match('[0-9a-fA-F]+$', keysym[1:]):
               	return atoi(keysym[1:], 16)
       	elif keysym[:2] == '0x' and match('[0-9a-fA-F]+$', keysym[2:]):
		return atoi(keysym[2:], 16)
	else:
        	print 'keysymvalue: UNKNOWN{%(keysym)s}' % { "keysym": keysym }
               	sys.exit(-1)

def keysymunicodevalue(keysym, file = "n/a", linenum = 0):
	""" Extracts a value from the keysym """
	""" Find the value of keysym, using the data from keysyms """
	""" Use file and linenum to when reporting errors """
	if keysym == "":
		return 0
       	if keysymunicodedatabase.has_key(keysym):
               	return keysymunicodedatabase[keysym]
       	elif keysym[0] == 'U' and match('[0-9a-fA-F]+$', keysym[1:]):
               	return atoi(keysym[1:], 16)
       	elif keysym[:2] == '0x' and match('[0-9a-fA-F]+$', keysym[2:]):
		return atoi(keysym[2:], 16)
	else:
        	print 'keysymunicodevalue: UNKNOWN{%(keysym)s}' % { "keysym": keysym }
               	sys.exit(-1)

def rename_combining(seq):
	filtered_sequence = []
	for ks in seq:
		if findall('^combining_', ks):
			filtered_sequence.append(sub('^combining_', 'dead_', ks))
		else:
			filtered_sequence.append(ks)
	return filtered_sequence

def check_if_sequence_exists(allsequences, seq):
	seq_len = len(seq)
	for s in allsequences:
		if seq_len == len(s):
			for i in range(seq_len - 1):
				if seq[i] != s[i]:
					return False
			if i == seq_len - 2:
				return True
	return False

keysymunicodedatabase = process_keysymstxt()
keysymdatabase = process_gdkkeysymsh()
gtkoldsequences = process_gtkoldsequences()

print

if opt_win32:
	""" Process the compose sequences in gtk-win32-sequences.txt
	""" 
	try:
		composefile_win32 = open(FILENAME_COMPOSE_WIN32, 'r')
	except IOError, (errno, strerror):
		if not opt_quiet:
			print "I/O error(%s): %s" % (errno, strerror)
			print "Did not find the win32 compose file %s. Exiting..." % (FILENAME_COMPOSE_WIN32)
	except:
	        print "Unexpected error: ", sys.exc_info()[0]
	        sys.exit(-1)

	""" Parse the compose file in xorg_compose_sequences_win32 """
	xorg_compose_sequences_win32 = []
	xorg_compose_sequences_win32_algorithmic = []

	linenum_compose = 0
	for line in composefile_win32.readlines():
		linenum_compose += 1
		line = line.strip()
		if line is "" or match("^XCOMM", line) or match("^#", line):
			continue

		components = split(':', line)
		if len(components) != 2:
			print "Invalid line %(linenum_compose)d in %(filename)s: No sequence\
			/value pair found" % { "linenum_compose": linenum_compose, "filename": FILENAME_COMPOSE_WIN32 }
			exit(-1)
		(seq, val ) = split(':', line)
		seq = seq.strip()
		val = val.strip()
		raw_sequence = findall('\w+', seq)
		values = split('\s+', val)
		unichar_temp = split('"', values[0])
		unichar = unichar_temp[1]
		try:
			codepointstr = values[1]
		except IndexError:
			codepointstr = 'U' + str(ord(unichar.decode('utf-8')[0]))
		if raw_sequence[0][0] == 'U' and match('[0-9a-fA-F]+$', raw_sequence[0][1:]):
			raw_sequence[0] = '0x' + raw_sequence[0][1:]
		if codepointstr[0] == 'U' and match('[0-9a-fA-F]+$', codepointstr[1:]):
			codepoint = atoi(codepointstr[1:], 16)
		elif keysymunicodedatabase.has_key(codepointstr):
			try: 
				if keysymdatabase[codepointstr] != keysymunicodedatabase[codepointstr]:
					if opt_warnings:
						print "DIFFERENCE (nonfatal): 0x%(a)X 0x%(b)X" % { "a": keysymdatabase[codepointstr], 
										"b": keysymunicodedatabase[codepointstr]},
						print raw_sequence, codepointstr
				else:
					codepoint = keysymunicodedatabase[codepointstr]
			except KeyError:
				if opt_warnings:
					print "KEYERROR (nonfatal): ", codepointstr
				codepoint = keysymunicodedatabase[codepointstr]
		else:
			print
			print "Invalid codepoint %(cp)s at line %(linenum_compose)d in %(filename)s:\
			 %(line)s" % { "cp": codepointstr, "linenum_compose": linenum_compose, "filename": FILENAME_COMPOSE_WIN32, "line": line }
			exit(-1)
		sequence = rename_combining(raw_sequence)
		""" This is temporary filtering, because we need to get an updated Compose file with less sequences """
		if "Multi_key" not in sequence:
			""" Ignore for now >0xFFFF keysyms """
			if codepoint < 0xFFFF:
				original_sequence = copy(sequence)
				stats_sequence = copy(sequence)
				base = sequence.pop()
				basechar = keysymvalue(base, FILENAME_COMPOSE_WIN32, linenum_compose)
				
				if basechar < 0xFFFF:
					counter = 1
					unisequence = []
					not_normalised = True
					skipping_this = False
					for i in range(0, len(sequence)):
						bc = basechar
						unisequence.append(unichr(keysymunicodevalue(sequence.pop(), FILENAME_COMPOSE_WIN32, linenum_compose)))
						
					if skipping_this:
						unisequence = []
					for perm in all_permutations(unisequence):
						# print counter, original_sequence, unichr(basechar) + "".join(perm)
						# print counter, map(unichr, perm)
						normalized = normalize('NFC', unichr(basechar) + "".join(perm))
						if len(normalized) == 1:
							# print 'Base: %(base)s [%(basechar)s], produces [%(unichar)s] (0x%(codepoint)04X)' \
							# % { "base": base, "basechar": unichr(basechar), "unichar": unichar, "codepoint": codepoint },
							# print "Normalized: [%(normalized)s] SUCCESS %(c)d" % { "normalized": normalized, "c": counter }
							stats_sequence_data = map(keysymunicodevalue, stats_sequence)
							stats_sequence_data.append(normalized)
							xorg_compose_sequences_win32_algorithmic.append(stats_sequence_data)
							not_normalised = False
							break;
						counter += 1
					if not_normalised:
						original_sequence.append(codepoint)
						if check_if_sequence_exists(xorg_compose_sequences_win32, original_sequence):
							if not opt_quiet:
								print "WARNING: Got duplicate sequence:", original_sequence
						xorg_compose_sequences_win32.append(original_sequence)
					else:
						print "INFO: Sequence was normalised, thus not including:", original_sequence
				else:
					print "Error in base char !?!"
					exit(-2)
			else:
				print "OVER", sequence
				exit(-1)
		else:
			sequence.append(codepoint)
			if check_if_sequence_exists(xorg_compose_sequences_win32, sequence):
				if not opt_quiet:
					print "WARNING: Got duplicate sequence:", sequence
			else: 
				xorg_compose_sequences_win32.append(sequence)

	print win32seqs_file_start
	print win32seqs_file_middle
	for seq in xorg_compose_sequences_win32:
		for sym in seq[:-1]:
			print "%18s" % ("GDK_%(sym)s, " % { "sym": sym }),
		for i in range(len(seq[:-1]), 5):
			print "%18s" % "",
		print "0x%(codepoint)04d, " % { "codepoint": seq[-1] }
	print win32seqs_file_end
	exit(0)

""" Grab and open the compose file from upstream """
filename_compose = download_file(URL_COMPOSE)
try: 
	composefile = open(filename_compose, 'r')
except IOError, (errno, strerror):
	print "I/O error(%s): %s" % (errno, strerror)
	sys.exit(-1)
except:
	print "Unexpected error: ", sys.exc_info()[0]
	sys.exit(-1)

""" Look if there is a lookaside compose file in the current
    directory, and if so, open, then merge with upstream Compose file.
"""
try:
	composefile_lookaside = open(FILENAME_COMPOSE_LOOKASIDE, 'r')
except IOError, (errno, strerror):
	if not opt_quiet:
		print "I/O error(%s): %s" % (errno, strerror)
		print "Did not find the lookaside compose file %s. Continuing..." % (FILENAME_LOOKASIDE)
except:
        print "Unexpected error: ", sys.exc_info()[0]
        sys.exit(-1)


xorg_compose_sequences_raw = []
for seq in composefile.readlines():
	xorg_compose_sequences_raw.append(seq)
for seq in composefile_lookaside.readlines():
	xorg_compose_sequences_raw.append(seq)

""" Parse the compose file in  xorg_compose_sequences"""
xorg_compose_sequences = []
xorg_compose_sequences_algorithmic = []
linenum_compose = 0
for line in xorg_compose_sequences_raw:
	linenum_compose += 1
	line = line.strip()
	if line is "" or match("^XCOMM", line) or match("^#", line):
		continue

	components = split(':', line)
	if len(components) != 2:
		print "Invalid line %(linenum_compose)d in %(filename)s: No sequence\
		/value pair found" % { "linenum_compose": linenum_compose, "filename": filename_compose }
		exit(-1)
	(seq, val ) = split(':', line)
	seq = seq.strip()
	val = val.strip()
	raw_sequence = findall('\w+', seq)
	values = split('\s+', val)
	unichar_temp = split('"', values[0])
	unichar = unichar_temp[1]
	if len(unichar.decode('utf-8')) > 1:
		if unichar[0] != '\\': 	# Ignore escaped characters.
			# No codepoints that are >1 characters yet.
			# plane1 multiple
			multiseq = []
			# print 'Multiple:', 
			for item in raw_sequence:
				# print item,
				multiseq.append(item)
			if multisequence_maxseqlen < len(raw_sequence):
				multisequence_maxseqlen = len(raw_sequence)
			# print len(unichar.decode('utf-8')), 
			multicodepoint = []
			for item in unichar.decode('utf-8'):
				# print "U%04X " % ord(item),
				multicodepoint.append("U%04X" % ord(item))
			if multisequence_maxvallen < len(unichar.decode('utf-8')):
				multisequence_maxvallen = len(unichar.decode('utf-8'))
			# print
			multisequences[unichar.decode('utf-8')] = [multiseq, multicodepoint]
			continue
	#if len(values) == 1:
		# print "SKIPPING PLANE1:", len(unichar.decode('utf-8')), tuple(values[0])
	#	continue
	#print values, tuple(unichar)
	try:
		codepointstr = values[1]
	except IndexError:
		codepointstr = 'U' + str(ord(unichar.decode('utf-8')[0]))
	if raw_sequence[0][0] == 'U' and match('[0-9a-fA-F]+$', raw_sequence[0][1:]):
		raw_sequence[0] = '0x' + raw_sequence[0][1:]
	if codepointstr[0] == 'U' and match('[0-9a-fA-F]+$', codepointstr[1:]):
		codepoint = atoi(codepointstr[1:], 16)
	elif keysymunicodedatabase.has_key(codepointstr):
		try: 
			if keysymdatabase[codepointstr] != keysymunicodedatabase[codepointstr]:
				if opt_warnings:
					print "DIFFERENCE (nonfatal): 0x%(a)X 0x%(b)X" % { "a": keysymdatabase[codepointstr], 
									"b": keysymunicodedatabase[codepointstr]},
					print raw_sequence, codepointstr
			else:
				codepoint = keysymunicodedatabase[codepointstr]
		except KeyError:
			if opt_warnings:
				print "KEYERROR (nonfatal): ", codepointstr
			codepoint = keysymunicodedatabase[codepointstr]
	else:
		print
		print "Invalid codepoint %(cp)s at line %(linenum_compose)d in %(filename)s:\
		 %(line)s" % { "cp": codepointstr, "linenum_compose": linenum_compose, "filename": filename_compose, "line": line }
		exit(-1)
	sequence = rename_combining(raw_sequence)
	if "dead_currency" in sequence:
		continue
	reject_this = False
	for i in sequence:
		if keysymvalue(i) > 0xFFFF:
			reject_this = True
			if opt_plane1:
				print 'Plane1:', sequence
			break
	if reject_this:
		continue
	for i in range(len(sequence)):
		if sequence[i] == "0x0342":
			sequence[i] = "dead_tilde"
	if "U0313" in sequence or "U0314" in sequence or "0x0313" in sequence or "0x0314" in sequence:
		continue
	""" This is temporary filtering, because we need to get an updated Compose file with less sequences """
	if "Multi_key" not in sequence:
		""" Ignore for now >0xFFFF keysyms """
		if codepoint < 0xFFFF:
			original_sequence = copy(sequence)
			stats_sequence = copy(sequence)
			base = sequence.pop()
			basechar = keysymvalue(base, filename_compose, linenum_compose)
			
			if basechar < 0xFFFF:
				counter = 1
				unisequence = []
				not_normalised = True
				skipping_this = False
				for i in range(0, len(sequence)):
					bc = basechar
					unisequence.append(unichr(keysymunicodevalue(sequence.pop(), filename_compose, linenum_compose)))
					
				if skipping_this:
					unisequence = []
				for perm in all_permutations(unisequence):
					# print counter, original_sequence, unichr(basechar) + "".join(perm)
					# print counter, map(unichr, perm)
					normalized = normalize('NFC', unichr(basechar) + "".join(perm))
					if len(normalized) == 1:
						# print 'Base: %(base)s [%(basechar)s], produces [%(unichar)s] (0x%(codepoint)04X)' \
						# % { "base": base, "basechar": unichr(basechar), "unichar": unichar, "codepoint": codepoint },
						# print "Normalized: [%(normalized)s] SUCCESS %(c)d" % { "normalized": normalized, "c": counter }
						stats_sequence_data = map(keysymunicodevalue, stats_sequence)
						stats_sequence_data.append(normalized)
						xorg_compose_sequences_algorithmic.append(stats_sequence_data)
						not_normalised = False
						break;
					counter += 1
				if not_normalised:
					original_sequence.append(codepoint)
					if check_if_sequence_exists(xorg_compose_sequences, original_sequence):
						if not opt_quiet:
							print "WARNING: Got duplicate sequence:", original_sequence
					xorg_compose_sequences.append(original_sequence)
					""" print xorg_compose_sequences[-1] """
					
			else:
				print "Error in base char !?!"
				exit(-2)
		else:
			print "OVER", sequence
			exit(-1)
	else:
		sequence.append(codepoint)
		if check_if_sequence_exists(xorg_compose_sequences, sequence):
			if not opt_quiet:
				print "WARNING: Got duplicate sequence:", sequence
		xorg_compose_sequences.append(sequence)
		""" print xorg_compose_sequences[-1] """

def sequence_cmp(x, y):
	if keysymvalue(x[0]) > keysymvalue(y[0]):
		return 1
	elif keysymvalue(x[0]) < keysymvalue(y[0]):
		return -1
	elif len(x) > len(y):
		return 1
	elif len(x) < len(y):
		return -1
	elif keysymvalue(x[1]) > keysymvalue(y[1]):
		return 1
	elif keysymvalue(x[1]) < keysymvalue(y[1]):
		return -1
	elif len(x) < 4:
		return 0
	elif keysymvalue(x[2]) > keysymvalue(y[2]):
		return 1
	elif keysymvalue(x[2]) < keysymvalue(y[2]):
		return -1
	elif len(x) < 5:
		return 0
	elif keysymvalue(x[3]) > keysymvalue(y[3]):
		return 1
	elif keysymvalue(x[3]) < keysymvalue(y[3]):
		return -1
	elif len(x) < 6:
		return 0
	elif keysymvalue(x[4]) > keysymvalue(y[4]):
		return 1
	elif keysymvalue(x[4]) < keysymvalue(y[4]):
		return -1
	else:
		return 0

def sequence_unicode_cmp(x, y):
	if keysymunicodevalue(x[0]) > keysymunicodevalue(y[0]):
		return 1
	elif keysymunicodevalue(x[0]) < keysymunicodevalue(y[0]):
		return -1
	elif len(x) > len(y):
		return 1
	elif len(x) < len(y):
		return -1
	elif keysymunicodevalue(x[1]) > keysymunicodevalue(y[1]):
		return 1
	elif keysymunicodevalue(x[1]) < keysymunicodevalue(y[1]):
		return -1
	elif len(x) < 4:
		return 0
	elif keysymunicodevalue(x[2]) > keysymunicodevalue(y[2]):
		return 1
	elif keysymunicodevalue(x[2]) < keysymunicodevalue(y[2]):
		return -1
	elif len(x) < 5:
		return 0
	elif keysymunicodevalue(x[3]) > keysymunicodevalue(y[3]):
		return 1
	elif keysymunicodevalue(x[3]) < keysymunicodevalue(y[3]):
		return -1
	elif len(x) < 6:
		return 0
	elif keysymunicodevalue(x[4]) > keysymunicodevalue(y[4]):
		return 1
	elif keysymunicodevalue(x[4]) < keysymunicodevalue(y[4]):
		return -1
	else:
		return 0

def sequence_algorithmic_cmp(x, y):
	if len(x) < len(y):
		return -1
	elif len(x) > len(y):
		return 1
	else:
		for i in range(len(x)):
			if x[i] < y[i]:
				return -1
			elif x[i] > y[i]:
				return 1
	return 0


xorg_compose_sequences.sort(sequence_cmp)

xorg_compose_sequences_uniqued = []
first_time = True
item = None
for next_item in xorg_compose_sequences:
	if first_time:
		first_time = False
		item = next_item
	if sequence_unicode_cmp(item, next_item) != 0:
		xorg_compose_sequences_uniqued.append(item)
	item = next_item

xorg_compose_sequences = copy(xorg_compose_sequences_uniqued)

counter_multikey = 0
for item in xorg_compose_sequences:
	if findall('Multi_key', "".join(item[:-1])) != []:
		counter_multikey += 1

xorg_compose_sequences_algorithmic.sort(sequence_algorithmic_cmp)
xorg_compose_sequences_algorithmic_uniqued = uniq(xorg_compose_sequences_algorithmic)

firstitem = ""
num_first_keysyms = 0
zeroes = 0
num_entries = 0
num_algorithmic_greek = 0
for sequence in xorg_compose_sequences:
	if keysymvalue(firstitem) != keysymvalue(sequence[0]): 
		firstitem = sequence[0]
		num_first_keysyms += 1
	zeroes += 6 - len(sequence) + 1
	num_entries += 1

for sequence in xorg_compose_sequences_algorithmic_uniqued:
	ch = ord(sequence[-1:][0])
	if ch >= 0x370 and ch <= 0x3ff or ch >= 0x1f00 and ch <= 0x1fff:
		num_algorithmic_greek += 1
		
if opt_algorithmic:
	for sequence in xorg_compose_sequences_algorithmic_uniqued:
		letter = "".join(sequence[-1:])
		print '0x%(cp)04X, %(uni)c, seq: [ <0x%(base)04X>,' % { 'cp': ord(unicode(letter)), 'uni': letter, 'base': sequence[-2] },
		for elem in sequence[:-2]:
			print "<0x%(keysym)04X>," % { 'keysym': elem },
		# Yeah, verified... We just want to keep the output similar to -u, so we can compare/sort easily 
		print "], recomposed as", letter, "verified"

def num_of_keysyms(seq):
	return len(seq) - 1

def convert_UnotationToHex(arg):
	if isinstance(arg, str):
		if match('^U[0-9A-F][0-9A-F][0-9A-F][0-9A-F]$', arg):
			return sub('^U', '0x', arg)
	return arg

def addprefix_GDK(arg):
	if match('^0x', arg):
		return '%(arg)s, ' % { 'arg': arg } 
	else:
		return 'GDK_%(arg)s, ' % { 'arg': arg } 

if opt_gtk:
	first_keysym = ""
	sequence = []
	compose_table = []
	ct_second_part = []
	ct_sequence_width = 2
	start_offset = num_first_keysyms * (WIDTHOFCOMPOSETABLE+1)
	we_finished = False
	counter = 0

	sequence_iterator = iter(xorg_compose_sequences)
	sequence = sequence_iterator.next()
	while True:
		first_keysym = sequence[0]					# Set the first keysym
		compose_table.append([first_keysym, 0, 0, 0, 0, 0])
		while sequence[0] == first_keysym:
			compose_table[counter][num_of_keysyms(sequence)-1] += 1
			try:
				sequence = sequence_iterator.next()
			except StopIteration:
				we_finished = True
				break
		if we_finished:
			break
		counter += 1

	ct_index = start_offset
	for line_num in range(len(compose_table)):
		for i in range(WIDTHOFCOMPOSETABLE):
			occurences = compose_table[line_num][i+1]
			compose_table[line_num][i+1] = ct_index
			ct_index += occurences * (i+2)

	for sequence in xorg_compose_sequences:
		ct_second_part.append(map(convert_UnotationToHex, sequence))

	print headerfile_start
	for i in compose_table:
		if opt_gtkexpanded:
			print "0x%(ks)04X," % { "ks": keysymvalue(i[0]) },
			print '%(str)s' % { 'str': "".join(map(lambda x : str(x) + ", ", i[1:])) }
		elif not match('^0x', i[0]):
			print 'GDK_%(str)s' % { 'str': "".join(map(lambda x : str(x) + ", ", i)) }
		else:
			print '%(str)s' % { 'str': "".join(map(lambda x : str(x) + ", ", i)) }
	for i in ct_second_part:
		if opt_numeric:
			for ks in i[1:][:-1]:
				print '0x%(seq)04X, ' % { 'seq': keysymvalue(ks) },
			print '0x%(cp)04X, ' % { 'cp':i[-1] }
			"""
			for ks in i[:-1]:
				print '0x%(seq)04X, ' % { 'seq': keysymvalue(ks) },
			print '0x%(cp)04X, ' % { 'cp':i[-1] }
			"""
		elif opt_gtkexpanded:
			print '%(seq)s0x%(cp)04X, ' % { 'seq': "".join(map(addprefix_GDK, i[:-1])), 'cp':i[-1] }
		else:
			print '%(seq)s0x%(cp)04X, ' % { 'seq': "".join(map(addprefix_GDK, i[:-1][1:])), 'cp':i[-1] }
	print headerfile_end 

def redecompose(codepoint):
	(name, decomposition, combiningclass) = unicodedatabase[codepoint]
	if decomposition[0] == '' or decomposition[0] == '0':
		return [codepoint]
	if match('<\w+>', decomposition[0]):
		numdecomposition = map(stringtohex, decomposition[1:])
		return map(redecompose, numdecomposition)
	numdecomposition = map(stringtohex, decomposition)
	return map(redecompose, numdecomposition)

def process_unicodedata_file(quiet = False):
	""" Grab from wget http://www.unicode.org/Public/UNIDATA/UnicodeData.txt """
	filename_unicodedatatxt = download_file(URL_UNICODEDATATXT)
	try: 
		unicodedatatxt = open(filename_unicodedatatxt, 'r')
	except IOError, (errno, strerror):
		print "I/O error(%s): %s" % (errno, strerror)
		sys.exit(-1)
	except:
		print "Unexpected error: ", sys.exc_info()[0]
		sys.exit(-1)
	for line in unicodedatatxt.readlines():
		if line[0] == "" or line[0] == '#':
			continue
		line = line[:-1]
		uniproperties = split(';', line)
		codepoint = stringtohex(uniproperties[0])
		""" We don't do Plane 1 or CJK blocks. The latter require reading additional files. """
		if codepoint > 0xFFFF or (codepoint >= 0x4E00 and codepoint <= 0x9FFF) or (codepoint >= 0xF900 and codepoint <= 0xFAFF): 
			continue
		name = uniproperties[1]
		category = uniproperties[2]
		combiningclass = uniproperties[3]
		decomposition = uniproperties[5]
		unicodedatabase[codepoint] = [name, split('\s+', decomposition), combiningclass]
	
	counter_combinations = 0
	counter_combinations_greek = 0
	counter_entries = 0
	counter_entries_greek = 0

	for item in unicodedatabase.keys():
		(name, decomposition, combiningclass) = unicodedatabase[item]
		if decomposition[0] == '':
			continue
			print name, "is empty"
		elif match('<\w+>', decomposition[0]):
			continue
			print name, "has weird", decomposition[0]
		else:
			sequence = map(stringtohex, decomposition)
			chrsequence = map(unichr, sequence)
			normalized = normalize('NFC', "".join(chrsequence))
			
			""" print name, sequence, "Combining: ", "".join(chrsequence), normalized, len(normalized),  """
			decomposedsequence = []
			for subseq in map(redecompose, sequence):
				for seqitem in subseq:
					if isinstance(seqitem, list):
						for i in seqitem:
							if isinstance(i, list):
								for j in i:
									decomposedsequence.append(j)
							else:
								decomposedsequence.append(i)
					else:
						decomposedsequence.append(seqitem)
			recomposedchar = normalize('NFC', "".join(map(unichr, decomposedsequence)))
			if len(recomposedchar) == 1 and len(decomposedsequence) > 1:
				counter_entries += 1
				counter_combinations += factorial(len(decomposedsequence)-1)
				ch = item
				if ch >= 0x370 and ch <= 0x3ff or ch >= 0x1f00 and ch <= 0x1fff:
					counter_entries_greek += 1
					counter_combinations_greek += factorial(len(decomposedsequence)-1)
				if not quiet and 0:
					print "0x%(cp)04X, %(uni)c, seq:" % { 'cp':item, 'uni':unichr(item) },
					print "[",
					for elem in decomposedsequence:
						print '<0x%(hex)04X>,' % { 'hex': elem },
					print "], recomposed as", recomposedchar,
					if unichr(item) == recomposedchar:
						print "verified"
	
	if not quiet:
		print "Unicode statistics from UnicodeData.txt"
		print "Number of entries that can be algorithmically produced     :", counter_entries
		print "  of which are for Greek                                   :", counter_entries_greek
		print "Number of compose sequence combinations requiring          :", counter_combinations
		print "  of which are for Greek                                   :", counter_combinations_greek
		print "Note: We do not include partial compositions, "
		print "thus the slight discrepancy in the figures"
		print

if opt_unicodedatatxt:
	process_unicodedata_file(True)

def is_composed(seq):
	unisequence = []
	not_normalised = True
	for i in range(len(seq[:-1])):
		if seq[i+1] == 'EMPTY' or i == 4:
			break
		# print ' adding(%(a)s)%(b)s' % { 'a': i, 'b': unichr(keysymunicodevalue(seq[i])) }
		unisequence.append(unichr(keysymunicodevalue(seq[i], filename_compose)))
	basechar = seq[i]
	# print ' basechar:', basechar, unichr(keysymunicodevalue(basechar))
		
	if i != 0:
		for perm in all_permutations(unisequence):
			# normalized = normalize('NFC', unichr(keysymunicodevalue(basechar)) + "".join(perm))
			normalized = normalize('NFC', "".join(perm))
			if len(normalized) == 1:
				# print " NORMALISED"
				return True
			else:
				pass
				# print " NOT normalised", normalized
	return False

if opt_regression:
	for seq in xorg_compose_sequences: # foreach xorg_compose_sequence [dead_acute, a, 291]
		if gtkoldsequences.has_key(seq[-1]): # if 219:
			seqexpanded = []
			for i in range(len(seq) - 1):
				seqexpanded.append(seq[i])
			for i in range(len(seq) - 1, 5):
				seqexpanded.append('EMPTY')
			seqexpanded.append(seq[-1])
			## print "Got common codepoint 0x%(a)04X %(b)s" % { 'a': int(seq[-1]), 'b': seqexpanded }
			for subseqi in range(len(gtkoldsequences[seq[-1]])):#[[dead_acute,a,0,0,0,291, False],[dead_acute,e,0,0,0,296,False]]
				wematched = True
				## print " ", "           comparing with", gtkoldsequences[seqexpanded[-1]][subseqi]
				for i in range(len(seqexpanded) - 1):
					## print "  ", i, seqexpanded[i], "with", gtkoldsequences[seq[-1]][subseqi][i]
					if seqexpanded[i] != gtkoldsequences[seqexpanded[-1]][subseqi][i]:
						if keysymvalue(seqexpanded[i]) != keysymvalue(gtkoldsequences[seqexpanded[-1]][subseqi][i]):
							wematched = False
							break
			
				if wematched:
					gtkoldsequences[seq[-1]][subseqi][-1] = True
					## print "MATCH                    ", gtkoldsequences[seq[-1]][subseqi]
					break
			## print
	seq_counter = 0
	for cp in gtkoldsequences.keys():
		for seq in gtkoldsequences[cp]:
			if seq[-1] == False:
				if is_composed(seq[:-1]):
					pass
					# print "WAS_COMPOSED", seq
				else:
					for s in seq[:-2]:
						if s == 'EMPTY':
							print "0",
						else:
							print "<%(a)s>" % { 'a': s },
					print "\t\t\t: \"%(a)c\" U%(b)04X" % { 'a': unichr(seq[-2]), 'b': seq[-2] }
					seq_counter += 1
					#print " ORPHAN", seq, "0x%04X" % seq[-2]
	print "XCOMM We have", seq_counter, "sequences"

def convert_unotation_to_hex(var):
	return "0x%04X" % atoi(var[1:], 16)


if opt_multiple:
	print multipleseqs_file_start
	print "static const gint compose_multi_max_sequence_len = %d;" % multisequence_maxseqlen
	print "static const gint compose_multi_max_codepoint_len = %d;" % multisequence_maxvallen
	# Index size can be deduced. Duh.
	# print "static const gint compose_multi_index_size = %d;" % len(multisequences)
	print multipleseqs_file_middle
	for i in multisequences:
		(seqs, vals) = multisequences[i]
		for s in range(len(seqs)):
			print '%6s,' % convert_unotation_to_hex(seqs[s]),
		for s in range(len(seqs), multisequence_maxseqlen):
			print '     0,',
		for s in range(len(vals)):
			print '%6s,' % convert_unotation_to_hex(vals[s]),
		for s in range(len(vals), multisequence_maxvallen):
			print '     0,',
		print
	print multipleseqs_file_end
	exit(0)

if opt_statistics:
	print
	print "Total number of compose sequences (from file)              :", len(xorg_compose_sequences) + len(xorg_compose_sequences_algorithmic)
	print "  of which can be expressed algorithmically                :", len(xorg_compose_sequences_algorithmic)
	print "  of which cannot be expressed algorithmically             :", len(xorg_compose_sequences) 
	print "    of which have Multi_key                                :", counter_multikey
	print 
	print "Algorithmic (stats for Xorg Compose file)"
	print "Number of sequences off due to algo from file (len(array)) :", len(xorg_compose_sequences_algorithmic)
	print "Number of sequences off due to algo (uniq(sort(array)))    :", len(xorg_compose_sequences_algorithmic_uniqued)
	print "  of which are for Greek                                   :", num_algorithmic_greek
	print 
	process_unicodedata_file()
	print "Not algorithmic (stats from Xorg Compose file)"
	print "Number of sequences                                        :", len(xorg_compose_sequences) 
	print "Flat array looks like                                      :", len(xorg_compose_sequences), "rows of 6 integers (2 bytes per int, or 12 bytes per row)"
	print "Flat array would have taken up (in bytes)                  :", num_entries * 2 * 6, "bytes from the GTK+ library"
	print "Number of items in flat array                              :", len(xorg_compose_sequences) * 6
	print "  of which are zeroes                                      :", zeroes, "or ", (100 * zeroes) / (len(xorg_compose_sequences) * 6), " per cent"
	print "Number of different first items                            :", num_first_keysyms
	print "Number of max bytes (if using flat array)                  :", num_entries * 2 * 6
	print "Number of savings                                          :", zeroes * 2 - num_first_keysyms * 2 * 5
	print 
	print "Memory needs if both algorithmic+optimised table in latest Xorg compose file"
	print "                                                           :", num_entries * 2 * 6 - zeroes * 2 + num_first_keysyms * 2 * 5
	print
	print "Old implementation in GTK+"
	print "Number of sequences in old gtkimcontextsimple.c            :", 691
	print "The existing (old) implementation in GTK+ used to take up  :", 691 * 2 * 12, "bytes"
