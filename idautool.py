#!/usr/bin/env python
"""Set IDAU boundary registers for Renesas RA TrustZone MCUs"""

usage = "%prog ELFFILE"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2021 Henrik Maier. All rights reserved."
__license__ = "SPDX-License-Identifier: Apache-2.0"

import re, sys, os, optparse, time
try:
    import winreg
except:
    sys.exit("error: Currently only Windows is supported!")
try:
    from elftools.elf.elffile import ELFFile
except:
    sys.exit("error: Requires pyelftools installed (Install with pip install pyelftools)!")


g_verbose = False


#
# Helper functions
#

def error(msg):
    """Prints error message and exists program"""
    sys.exit("%s error: %s!" % (os.path.basename(sys.argv[0]), msg))


def findRenesasRfpTool():
    """Searches for an installed Renesas Flash Programmer tool in the Windows registry"""
    try:
        registry = winreg.ConnectRegistry(None,winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(registry,r"SOFTWARE\Classes\rpjfile\shell\Open\command")
        val = winreg.QueryValue(key, None)
        match = re.match(r'"(.*?)".*', val)[1]
        path = os.path.dirname(match)    
        return os.path.join(path, 'rfp-cli.exe')
    except:
        error("Renesas Flash Programmer must be installed (https://www.renesas.com/rfp)")


def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell (Windows and Unix)."""
    if os.name in ['nt', 'dos', 'os2']:
        # use Dos style command shell for NT, DOS and OS/2
        pipe = os.popen(cmd + ' 2>&1', 'r')
    else:
        # use Unix style for all others
        pipe = os.popen('{ ' + cmd + '; } 2>&1', 'r')
    text = pipe.read()
    sts = pipe.close()
    if sts is None: sts = 0
    if text[-1:] == '\n': text = text[:-1]
    return sts, text


def execute(cmd, argStr):
    """Execute shell commands"""
    cmdLine = '"' + cmd + '" ' + argStr
    if g_verbose:
        print("Execute: %s" % cmdLine)
    status, output = getstatusoutput(cmdLine)
    if status != 0:
        print(output)
        error("Command execution failed")
    return output


def readSymbol(symbols, name):
    """Reads a symbols from symbol table and returns its address"""
    try:
        sym = symbols.get_symbol_by_name(name)
        address = sym[0]['st_value']
        size = sym[0]['st_size']
    except:
        error("Could not find symbol %s in ELF file" % name)
    if (g_verbose):
        print("%s 0x%x" % (name, address))
    return address


def main():
    """Main program - called when run as a script."""
    global g_verbose

    #
    # Command line options
    #
    print(__doc__)
    parser = optparse.OptionParser(usage, version="%%prog %s" % __version__)
    parser.add_option("-v", "--verbose", action="store_true", help="verbose mode")
    parser.add_option("-t", "--tool", default="jlink", help="programming tool (jlink, e2 or e2l)")
    parser.add_option("-d", "--dryrun", action="store_true", help="dry run, don't change anything, print command line only")
    options, args = parser.parse_args()
    if len(args) > 1:
        parser.error("Too many arguments")
    if len(args) < 1:
        parser.error("No input ELF file")
    g_verbose = options.verbose
    if options.tool == "jlink":
        toolOptions = "jlink -speed 115200"
    else:
        toolOptions = options.emuType
    argStr = "-noprogress -d ra -t %s " % toolOptions

    rfpCliPath = findRenesasRfpTool()

    #
    # Process ELF file
    #
    try:
        f = open(args[0], 'rb')
    except:
        parser.error("Could not find ELF file %s" % args[0])
    elf = ELFFile(f)

    #
    # Find the symbol table.
    #
    try:
        symtab = elf.get_section_by_name('.symtab')
    except:
        error("Could not find symbol table in ELF file")
    if (g_verbose):
        print("Reading boundary sysmbols:")

    #
    # Code Flash -idauCFS, -idauCFNSC
    #
    s = readSymbol(symtab, '__tz_FLASH_S')
    c = readSymbol(symtab, '__tz_FLASH_C')
    n = readSymbol(symtab, '__tz_FLASH_N')
    idauCFS = (c - s) // 1024
    idauCFNSC = (n - c) // 1024

    #
    # Data Flash -idauDFS
    #
    s = readSymbol(symtab, '__tz_DATA_FLASH_S')
    n = readSymbol(symtab, '__tz_DATA_FLASH_N')
    idauDFS = (n - s) // 1024

    #
    # SRAM -idauSRAMS, -idauSRAMNSC
    #
    s = readSymbol(symtab, '__tz_RAM_S')
    c = readSymbol(symtab, '__tz_RAM_C')
    n = readSymbol(symtab, '__tz_RAM_N')
    idauSRAMS = (c - s) // 1024
    idauSRAMNSC = (n - c) // 1024

    f.close()
    startTime = time.time()        

    #
    # Run the Renesas command line tool to check current settings
    #
    if options.dryrun:
        match = [-1, -1, -1, -1, -1] # Force change to be detected
    else:
        output = execute(rfpCliPath, argStr + "-rfo")
        try:
            match = re.search('Boundary: (\d+),(\d+),(\d+),(\d+),(\d+)$', output, re.MULTILINE)
            if match.lastindex != 5:
                raise Exception()
            if (g_verbose):
                print(re.sub(r'\n\s*\n','\n', output, re.MULTILINE)) # Print output with empty lines removed
        except:
            print(output)
            error("Error parsing tool output")

    #
    # Run the Renesas command line tool to program updated settings
    #
    if idauCFS == int(match[1]) and idauCFNSC == int(match[2]) and idauDFS == int(match[3]) and idauSRAMS == int(match[4]) and idauSRAMNSC == int(match[5]):
        print("IDAU boundary registers are already correctly set, no change.")
    else:
        print("IDAU boundary registers are different, re-programming...")
        cmdStr = "-noverify-fo -fo boundary %u,%u,%u,%u,%u -p" % (idauCFS, idauCFNSC, idauDFS, idauSRAMS, idauSRAMNSC)
        if options.dryrun:
            print("Command line: %s %s" % (rfpCliPath, argStr + cmdStr))
            sys.exit(0)
        output = execute(rfpCliPath, argStr + cmdStr)
        if (g_verbose):
            print(re.sub(r'\n\s*\n','\n', output, re.MULTILINE)) # Print output with empty lines removed

    if (g_verbose):
        executionTime = (time.time() - startTime)
        print("Execution time: %0.2fs" % executionTime)

    print()
    print("\tCode Flash Secure %4d KB" % (idauCFS))
    print("\tCode Flash NSC    %4d KB" % (idauCFNSC))
    print("\tData Flash Secure %4d KB" % (idauDFS))
    print("\tSRAM Secure       %4d KB" % (idauSRAMS))
    print("\tSRAM NSC          %4d KB" % (idauSRAMNSC))


if __name__ == "__main__":
    main()
