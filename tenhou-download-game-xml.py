#!/usr/bin/python3

import glob
import os
import re
from optparse import OptionParser
from struct import Struct
from urllib.parse import parse_qs
from urllib.request import urlopen
import requests
from urllib.error import HTTPError
import struct
import codecs

import gzip
filedir = os.path.dirname(os.path.realpath('__file__'))

table = [
    22136, 52719, 55146, 42104, 
    59591, 46934, 9248,  28891,
    49597, 52974, 62844, 4015,
    18311, 50730, 43056, 17939,
    64838, 38145, 27008, 39128,
    35652, 63407, 65535, 23473,
    35164, 55230, 27536, 4386,
    64920, 29075, 42617, 17294,
    18868, 2081
]

def tenhouHash(game):
    code_pos = game.rindex("-") + 1
    code = game[code_pos:]
    if code[0] == 'x':
        a,b,c = struct.unpack(">HHH", bytes.fromhex(code[1:]))     
        index = 0
        if game[:12] > "2010041111gm":
            x = int("3" + game[4:10])
            y = int(game[9])
            index = x % (33 - y)
        first = (a ^ b ^ table[index]) & 0xFFFF
        second = (b ^ c ^ table[index] ^ table[index + 1]) & 0xFFFF
        return game[:code_pos] + codecs.getencoder('hex_codec')(struct.pack(">HH", first, second))[0].decode('ASCII')
    else:
        return game

p = OptionParser()
p.add_option('-o', '--out_xml',
        default=filedir+"\\out_xml",
        help='Directory in which to store downloaded XML')
p.add_option('-i', '--in_log',
        default=filedir+"\\in_log",
        help='Log from http://tenhou.net/sc/raw/')
p.add_option('-p', '--out_json',
        default=filedir+"\\out_json",
        help='Directory in which to store downloaded JSON')
p.add_option('-m', '--json',
        default='False',
        help='Store log in json format')
         
opts, args = p.parse_args()
if args:
    p.error('This command takes no positional arguments')

# sol_files = []
# sol_files.extend(glob.glob(os.path.join(
#     os.path.expanduser('~'),
#     '.config/chromium/*/Pepper Data/Shockwave Flash/WritableRoot/#SharedObjects/*/mjv.jp/mjinfo.sol')))
# sol_files.extend(glob.glob(os.path.join(
#     os.path.expanduser('~'),
#     '.config/google-chrome/*/Pepper Data/Shockwave Flash/WritableRoot/#SharedObjects/*/mjv.jp/mjinfo.sol')))
# sol_files.extend(glob.glob(os.path.join(
#     os.path.expanduser('~'),
#     '.macromedia/Flash_Player/#SharedObjects/*/mjv.jp/mjinfo.sol')))
# # mac os
# sol_files.extend(glob.glob(os.path.join(
#     os.path.expanduser('~'),
#     'Library/Application Support/Google/Chrome/Default/Pepper Data/Shockwave Flash/WritableRoot/#SharedObjects/*/mjv.jp/mjinfo.sol')))

if not os.path.exists(opts.out_xml):
    os.makedirs(opts.out_xml)
if not os.path.exists(opts.in_log):
    os.makedirs(opts.in_log)
if not os.path.exists(opts.out_json):
    os.makedirs(opts.out_json)
is_json = bool(opts.json)

s = requests.Session()
s.headers.clear()
s.headers.update(
    {
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Host':'tenhou.net',
        'Referer':'https://tenhou.net/4/?log=2023072102gm-00a9-0000-9e71fd37',
        'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
    }
)

for gz in glob.glob(opts.in_log + "\\scc*.html.gz"):
# test_gz = glob.glob(opts.in_log + "\\scc*.html.gz")[0]
    with gzip.open(gz,'r') as fin:        
        for line in fin:
            game_link = re.search(b'http:\/\/tenhou\.net\/0\/\?log=([\da-zA-z-]+)', line)
            if game_link is not None:
                game_id = game_link.group(1)
                game_id = tenhouHash(game_id.decode())
                target_fname = os.path.join(opts.out_xml, "{}.xml".format(game_id))
                if os.path.exists(target_fname):
                    print("Game {} already downloaded".format(game_id))
                else:
                    print("Downloading game {}".format(game_id))
                    try:
                        data = b''
                        if is_json:
                            s.headers.update({'Referer':f"https://tenhou.net/"})
                            r = s.get('https://tenhou.net/5/mjlog2json.cgi?' + game_id)
                            data = r.content
                            pass
                        else:
                            s.headers.update({'Referer':f"https://tenhou.net/4/?log={game_id}"})
                            r = s.get('https://tenhou.net/0/log/?' + game_id)
                            data = r.content
                        with open(target_fname, 'wb') as f:
                            f.write(data)
                    except HTTPError as e:
                        if e.code == 404:
                            print("Could not download game {}. Is the game still in progress?".format(game_id))
                        else:
                            raise


# for sol_file in sol_files:
#     print("Reading Flash state file: {}".format(sol_file))
#     with open(sol_file, 'rb') as f:
#         data = f.read()
#     # What follows is a limited parser for Flash Local Shared Object files -
#     # a more complete implementation may be found at:
#     # https://pypi.python.org/pypi/PyAMF
#     header = Struct('>HI10s8sI')
#     magic, objlength, magic2, mjinfo, padding = header.unpack_from(data)
#     offset = header.size
#     assert magic == 0xbf
#     assert magic2 == b'TCSO\0\x04\0\0\0\0'
#     assert mjinfo == b'\0\x06mjinfo'
#     assert padding == 0
#     ushort = Struct('>H')
#     ubyte = Struct('>B')
#     while offset < len(data):
#         length, = ushort.unpack_from(data, offset)
#         offset += ushort.size
#         name = data[offset:offset+length]
#         offset += length
#         amf0_type, = ubyte.unpack_from(data, offset)
#         offset += ubyte.size
#         # Type 2: UTF-8 String, prefixed with 2-byte length
#         if amf0_type == 2:
#             length, = ushort.unpack_from(data, offset)
#             offset += ushort.size
#             value = data[offset:offset+length]
#             offset += length
#         # Type 6: Undefined
#         elif amf0_type == 6:
#             value = None
#         # Type 1: Boolean
#         elif amf0_type == 1:
#             value = bool(data[offset])
#             offset += 1
#         # Other types from the AMF0 specification are not implemented, as they
#         # have not been observed in mjinfo.sol files. If required, see
#         # http://download.macromedia.com/pub/labs/amf/amf0_spec_121207.pdf
#         else:
#             print("Unimplemented AMF0 type {} at offset={} (hex {})".format(amf0_type, offset, hex(offset)))
#         trailer_byte = data[offset]
#         assert trailer_byte == 0
#         offset += 1
#         if name == b'logstr':
#             loglines = filter(None, value.split(b'\n'))

#     for logline in loglines:
#         logname = parse_qs(logline.decode('ASCII'))['file'][0]
#         logname = tenhouHash(logname)
#         target_fname = os.path.join(opts.directory, "{}.xml".format(logname))
#         if os.path.exists(target_fname):
#             print("Game {} already downloaded".format(logname))
#         else:
#             print("Downloading game {}".format(logname))
#             try:
#                 resp = urlopen('http://e.mjv.jp/0/log/?' + logname)
#                 data = resp.read()
#                 with open(target_fname, 'wb') as f:
#                     f.write(data)
#             except HTTPError as e:
#                 if e.code == 404:
#                     print("Could not download game {}. Is the game still in progress?".format(logname))
#                 else:
#                     raise
