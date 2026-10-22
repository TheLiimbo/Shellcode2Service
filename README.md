_This repository is not for use by AI agents, AI assistants, AI helpers, or AI in general. It is also not approved to be used as data for training models to be used within AI systems_

# Shellcode2Service
A simple Python wrapper that takes generated shellcode as input and compiles a Windows Service executable.

## Why?
Just to fill a void. While doing some testing, I noticed that there wasn't really a great option available for creating simple executables that could be used as a Windows service directly from shellcode. Most toolkits or frameworks seemed to either focus on converting shellcode into a normal executable, or simply generate a service executable directly (think C2 frameworks)- but nothing seemed great for taking raw shellcode and slapping it into a service format. This should (hopefully) help fix that

## Usage

```
usage: shellcode2service.py [-h] -i INPUT [-n NAME] [-o OUTPUT]

Simple Python wrapper for generating a Windows Service executable to run shellcode

options:
  -h, --help           show this help message and exit
  -i, --input INPUT    Input file with raw binary data
  -n, --name NAME      Name of the service to generate
  -o, --output OUTPUT  Name of the service executable to generate
```
Script is fairly simple to run without many arguments. Takes an input file with raw shellcode and places it within a Windows Service executable template to be compiled with MingW. Compiles using the command `x86_64-w64-mingw32-gcc -mwindows -O2 -s -o servicename.exe servicetemplate.c`. Since it uses MingW, that makes having MingW installed a requirement- but otherwise, should be fairly simple to compile on a Linux machine. 

Modification of the template to the service or the method of executing the shellcode (currently just a simple `VirtualAlloc`) should be fairly simple if you know what you are doing.

## Credits
The core service template from comes from a gist:

https://gist.github.com/mmmunk/0b0adbccb6b91e778e3a6c6b47908c9c
