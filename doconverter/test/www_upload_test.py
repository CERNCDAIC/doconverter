#!c:\Python34\python.exe
# -*- coding: utf-8 -*-

# Copyright (C) 2016, CERN
# This software is distributed under the terms of the GNU General Public
# Licence version 3 (GPL Version 3), copied verbatim in the file "LICENSE".
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as Intergovernmental Organization
# or submit itself to any jurisdiction.

import multiprocessing
import requests
import argparse
import random
import time
import sys
import os
import re
import shutil


url = None
url_response = None
files = []
diresponse = None


def give_me_a_number(high_value):
    '''It provides a random number between [0,high_value]

    :return: an int that should be between limits of the of possible files
    '''
    if not files:
        return 0
    a = random.randint(0, high_value)
    print(a)
    return a


def format_conversion(extension=None):
    '''Out of a predefined set e.g. pdf, pdfa, ps

    :param: extension of the file to be converted e.g. htm
    :return: one of the predefined types
    '''
    available = ['pdf', 'pdfa', 'ps']
    if extension in ['html']:
        available.remove('ps')
    return random.choice(available)


def send_by_web(filename):
    '''Send file to a certain URL

    :param filename: file to be sent for conversion
    :return:
    '''

    print('working with file %s ' % filename)
    m = re.match(r'.*\.(\w+)', filename)
    extension = None
    if m.groups():
        extension = m.group(1)
    fin = open(filename, 'rb')
    files = {'uploadedfile': fin}
    payload = {
        'converter': format_conversion(extension),
        'diresponse': r'XXXXXXXXXXXXXXXXX',
        'urlresponse': url_response,
    }
    try:
        r = requests.post(url, files=files, data=payload, verify=False)
        print(r.text)
    except:
        print("Unexpected error:", sys.exc_info()[0])
    finally:
        os.unlink(filename)
        fin.close()


def build_array_processes(iterations, POOLSIZE):
    '''

    :param iterations:
    :param POOLSIZE:
    :return:
    '''
    print('Poolsize: {}, totalnum: {}'.format(POOLSIZE, iterations))
    digest_pool = multiprocessing.Pool(POOLSIZE)
    allfiles = build_array_files(iterations, len(files) - 1)

    print('length allfiles %s: ' % len(allfiles))
    print('POOLSIZE %s: ' % POOLSIZE)
    print('Pool chunksize is %s: ' % round(len(allfiles)/POOLSIZE))
    digest_pool.imap_unordered(send_by_web, allfiles)
    digest_pool.close()
    digest_pool.join()


def format_filename(file, number):
    '''

    :param file:
    :return:
    '''
    (path, filename) = os.path.split(file)
    regexc = re.compile('(\w*)\.(\w{2,4})')
    matched = regexc.match(filename)
    if matched.groups():
        sequence = '{num:05d}'.format(num=number)
        new_filename = 'file{0}.{1}'.format(sequence, matched.group(2))
        print('filename is: %s' % new_filename)
        shutil.copyfile(file, os.path.join(path, new_filename))
        return os.path.join(path, new_filename)
    return None


def build_array_files(iteractions, nr_files):
    '''

    :param iterations: final array should have that quantity of files
    :return: array of files out of 'files' internal array
    '''
    arr = []
    for x in range(0, iteractions):
        file = files[give_me_a_number(nr_files)]
        newfile = format_filename(file, x)
        print('newfile is %s' % newfile)
        if newfile and os.path.exists(newfile):
            arr.append(newfile)
    print(arr)
    return arr


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Testing upload of file using multiprocesses')
    parser.add_argument('--n', action='store', type=int, dest='iterations', required=True,
                        help='number of files to send')
    parser.add_argument('--p', action='store', type=int, dest='POOLSIZE', required=True, help='Number of processes')
    parser.add_argument('--dest', action='store', type=str, dest='dest_url', required=False,
                        help='Destination URL')

    results = parser.parse_args()
    print(parser.parse_args())
    iterations = results.iterations
    POOLSIZE = results.POOLSIZE
    if results.dest_url:
        url = results.dest_url
    start = time.time()
    build_array_processes(iterations, POOLSIZE)
    print('{} run lasted (in seconds)'.format(time.time() - start))
