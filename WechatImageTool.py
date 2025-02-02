#!/usr/bin/env python
# zhangxiaoyang.hit[at]gmail.com

import re
import os

class WechatImageDecoder:
    def __init__(self, dat_file):
        dat_file = dat_file.lower()

        decoder = self._match_decoder(dat_file)
        decoder(dat_file)

    def _match_decoder(self, dat_file):
        decoders = {
            r'.+\.dat$': self._decode_pc_dat,
            r'cache\.data\.\d+$': self._decode_android_dat,
            None: self._decode_unknown_dat,
        }

        for k, v in decoders.items():
            if k is not None and re.match(k, dat_file):
                return v
        return decoders[None]

    def _decode_pc_dat(self, dat_file):
        
        def do_magic(header_code, buf):
            return header_code ^ list(buf)[0] if buf else 0x00
        
        def decode(magic, buf):
            return bytearray([b ^ magic for b in list(buf)])
            
        def guess_encoding(buf):
            headers = {
                'jpg': (0xff, 0xd8),
                'png': (0x89, 0x50),
                'gif': (0x47, 0x49),
            }
            for encoding in headers:
                header_code, check_code = headers[encoding] 
                magic = do_magic(header_code, buf)
                _, code = decode(magic, buf[:2])
                if check_code == code:
                    return (encoding, magic)
            print('Decode failed')
            sys.exit(1) 

        with open(dat_file, 'rb') as f:
            buf = bytearray(f.read())
        file_type, magic = guess_encoding(buf)

        img_file = re.sub(r'.dat$', '.' + file_type, dat_file)
        with open(img_file, 'wb') as f:
            new_buf = decode(magic, buf)
            f.write(new_buf)

    def _decode_android_dat(self, dat_file):
        with open(dat_file, 'rb') as f:
            buf = f.read()

        last_index = 0
        for i, m in enumerate(re.finditer(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46', buf)):
            if m.start() == 0:
                continue

            imgfile = '%s_%d.jpg' % (dat_file, i)
            with open(imgfile, 'wb') as f:
                f.write(buf[last_index: m.start()])
            last_index = m.start()

    def _decode_unknown_dat(self, dat_file):
        raise Exception('Unknown file type')

def findAllFile(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            if f.endswith('.dat'):
                fullname = os.path.join(root, f)
                yield fullname

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2 and len(sys.argv) != 1:
        print('\n'.join([
            'Usage:',
            '  python WechatImageDecoder.py [folder]',
            '',
            'Note: Default folder is current folder'
        ]))
        sys.exit(1)

    base = './'
    if len(sys.argv) == 2:
        _,  base = sys.argv[:2]

    AllFiles = list(findAllFile(base))
    total = len(AllFiles)
    print("Found " + str(total) + " files")
    count = 0
    for f in AllFiles:
        count = count + 1
        print ("Converting[" + str(count) + "/" + str(total) + "]:" + f, end="")
        try:
            WechatImageDecoder(f)
            print("......Done")
        except Exception as e:
            print("......Error")
            continue
    sys.exit(0)
