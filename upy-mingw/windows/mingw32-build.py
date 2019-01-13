#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#
#
#  Tips:
#   Micropython using preprocess to find all exist string
#   and convert this string to integer index
#   this can speed-up and save space.
#
from __future__ import print_function

import os
import stat
import glob
import subprocess


#-----------------------------------------------------------
CFLAGS_common = ' '.join(r'''
-I .
-I ..
-I ../windows
-I ../windows/msvc

-Wall
-Wpointer-arith
-ansi
-std=gnu99

-DMICROPY_NLR_SETJMP 
-DMICROPY_USE_READLINE=1
-DUNIX
-D__USE_MINGW_ANSI_STDIO=1
'''.splitlines())


CFLAGS_qstr_opt = ' '.join(r'''
-DNO_QSTR
-DN_X64
-DN_X86
-DN_THUMB
-DN_ARM

-Os
-E
'''.splitlines())


CFLAGS = ' '.join(r'''
-Os
-c
'''.splitlines())


#-----------------------------------------------------------
# assembly for setjmp and longjmp
#
ASMSRCS_ALL = [
    r'..\py\nlrx86.s'
    r'..\py\nlrx64.s'
    r'..\py\nlrxtensa.s'
]
ASMSRCS = []

CSRCS_ = [
    r'..\extmod\machine_mem.c',
    r'..\extmod\machine_pinbase.c',
    r'..\extmod\modubinascii.c',
    r'..\extmod\moductypes.c',
    r'..\extmod\moduhashlib.c',
    r'..\extmod\moduheapq.c',
    r'..\extmod\modujson.c',
    r'..\extmod\modurandom.c',
    r'..\extmod\modure.c',
    r'..\extmod\moduzlib.c',

    r'..\lib\mp-readline\*.c',

    r'..\py\*.c',

    r'..\unix\file.c',
    r'..\unix\gccollect.c',
    r'..\unix\input.c',
    r'..\unix\main.c',
    r'..\unix\modos.c',
    r'..\unix\modtime.c',
    r'..\unix\modmachine.c',

    r'..\windows\*.c',
    r'..\windows\msvc\*.c',
]

EXCLUDE_NATIVE = [
    r'..\py\asmarm.c',
    r'..\py\asmthumb.c',
    r'..\py\asmx86.c',
    r'..\py\asmx64.c',
]

CSRCS = []
for pattern in CSRCS_:
    CSRCS.extend(glob.glob(pattern))

CSRCS = list(filter(lambda v:v not in EXCLUDE_NATIVE, CSRCS))

#-----------------------------------------------------------
def file_put_contents(fn, d):
    f = open(fn, 'w', encoding='UTF-8')
    f.write(d)
    f.close()

def file_put_binary(fn, d):
    f = open(fn, 'wb')
    f.write(d)
    f.close()

def is_update(src, dst):
    if not os.path.isfile(dst):
        return True
    elif os.stat(src)[stat.ST_MTIME] > os.stat(dst)[stat.ST_MTIME]:
        return True
    return False

def qstr_optimize(CSRCS):
    global CFLAGS_common
    global CFLAGS_qstr_opt

    print('> create mpversion.h') 
    subprocess.check_call("python ../py/makeversionhdr.py genhdr/mpversion.h")

    print('> preprocess c files for QSTR optimize')
    c_pp_pairs = []
    for infn in CSRCS:
        infn = os.path.abspath(infn)
        outfn = infn
        for m, r in [("/", "__"), ("\\", "____"), (":", "@"), ("..", "@@")]:
            outfn = outfn.replace(m, r)
        outfn = "tmp/" + outfn + ".pp"
        c_pp_pairs.append((infn, outfn))

        if is_update(infn, outfn):
            print(' %s' % infn)
            cmd = ["gcc", CFLAGS_common, CFLAGS_qstr_opt, infn]
            res = subprocess.check_output(' '.join(cmd))
            file_put_binary(outfn, res)

    print('> analysis qstr')
    for cfn, ppfn in c_pp_pairs:
        outfn = os.path.abspath(cfn)
        for m, r in [("/", "__"), ("\\", "____"), (":", "@"), ("..", "@@")]:
            outfn = outfn.replace(m, r)
        outfn = "genhdr/qstr/" + outfn + ".qstr"

        if is_update(ppfn, outfn):
            print(' %s' % ppfn)
            cmd = ['python', '../py/makeqstrdefs.py', 
                   'split', ppfn, 'genhdr/qstr', 'genhdr/qstrdefscollected.h']
            subprocess.check_call(' '.join(cmd))
        else:
            print(' %s [skip]' % ppfn)

    print('> collect all qstr* to qstrdefscollected.h')
    cmd = ['python', '../py/makeqstrdefs.py',
           'cat', 'none',
           'genhdr/qstr', 
           'genhdr/qstrdefscollected.h']
    subprocess.check_call(' '.join(cmd))

    print('> create qstrdefspreprocessed.h ...')
    cmd = ['gcc', CFLAGS_common, CFLAGS_qstr_opt, '../py/qstrdefs.h', '../unix/qstrdefsport.h']
    res = subprocess.check_output(' '.join(cmd))
    file_put_binary("genhdr/qstrdefspreprocessed.h", res)

    print('> create rodata qstr to qstrdefs.generated.h')
    cmd = ['python', '../py/makeqstrdata.py',
            'genhdr/qstrdefspreprocessed.h',
            'genhdr/qstrdefscollected.h']
    res = subprocess.check_output(' '.join(cmd))
    file_put_binary("genhdr/qstrdefs.generated.h", res)

def build(CSRCS, ASMSRCS):
    global CFLAGS_common
    global CFLAGS

    for cfn in CSRCS:
        outfn = cfn
        for m, r in [("/", "__"), ("\\", "____"), (":", "@"), ("..", "@@")]:
            outfn = outfn.replace(m, r)
        outfn = 'tmp/' + outfn + '.o'

        if is_update(cfn, outfn):
            print(' %s' % cfn)
            cmd = ['gcc', CFLAGS_common, CFLAGS, cfn, '-o', outfn]
            subprocess.check_call(' '.join(cmd))

    for sfn in ASMSRCS:
        outfn = sfn
        for m, r in [("/", "__"), ("\\", "____"), (":", "@"), ("..", "@@")]:
            outfn = outfn.replace(m, r)
        outfn = 'tmp/' + outfn + '.o'

        print(' %s' % sfn)
        cmd = ['gcc', CFLAGS_common, CFLAGS, sfn, '-o', outfn]
        subprocess.check_call(' '.join(cmd))

    subprocess.check_call('gcc tmp/*.o -lm -o micropython')

if __name__ == '__main__':
    if not os.path.isdir('genhdr'):
        os.mkdir('genhdr')

    if not os.path.isdir('genhdr/qstr'):
        os.mkdir('genhdr/qstr')

    if not os.path.isdir('tmp'):
        os.mkdir('tmp')

    qstr_optimize(CSRCS)
    build(CSRCS, ASMSRCS)

