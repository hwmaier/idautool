#!/usr/bin/env python
"""Set IDAU boundary registers for Renesas RA6M5 MCUs"""

usage = "%prog ELFFILE"
__version__ = "0.2"
__copyright__ = "Copyright (c) 2021 Henrik Maier. All rights reserved."
__license__ = "MIT, http://opensource.org/licenses/MIT"

import re, sys, os, optparse
try:
    from elftools.elf.elffile import ELFFile
except:
    sys.exit("error: Requires pyelftools installed (Install with pip install pyelftools)!")


g_verbose = False

# There needs to be a better way to resolve the location of RenesasDevicePartitionManagerCmd
RDPM_PATH = r"c:\Users\%s\.eclipse\com.renesas.platform_1476787444\DebugComp\RA\DevicePartitionManager\RenesasDevicePartitionManagerCmd.exe" % os.environ.get('USERNAME')


#
# Helper functions
#

def error(msg):
    """Prints error message and exists program"""
    sys.exit("%s error: %s!" % (os.path.basename(sys.argv[0]), msg))


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
    cmdLine = cmd + ' ' + argStr
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
    parser.add_option("-e", "--emuType", default="jlink", help="emulator type (jlink, e2 or e2lite)")
    parser.add_option("-d", "--dryrun", action="store_true", help="dry run, don't change anything, print commandline only")
    options, args = parser.parse_args()
    if len(args) > 1:
        parser.error("Too many arguments")
    if len(args) < 1:
        parser.error("No input ELF file")
    g_verbose = options.verbose
    argStr = "-emuType %s -action BOUNDARY" % options.emuType

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
    idauCFS = (c - s) / 1024
    idauCFNSC = (n - c) / 1024
    argStr += " -idauCFS %u -idauCFNSC %u" % (idauCFS, idauCFNSC)

    #
    # Data Flash -idauDFS
    #
    s = readSymbol(symtab, '__tz_DATA_FLASH_S')
    n = readSymbol(symtab, '__tz_DATA_FLASH_N')
    idauDFS = (n - s) / 1024
    argStr += " -idauDFS %u" % (idauDFS)

    #
    # SRAM -idauSRAMS, -idauSRAMNSC
    #
    s = readSymbol(symtab, '__tz_RAM_S')
    c = readSymbol(symtab, '__tz_RAM_C')
    n = readSymbol(symtab, '__tz_RAM_N')
    idauSRAMS = (c - s) / 1024
    idauSRAMNSC = (n - c) / 1024
    argStr += " -idauSRAMS %u -idauSRAMNSC %u" % (idauSRAMS, idauSRAMNSC)

    f.close()

    # Run the Renesas command line tool
    if options.dryrun:
        print("Command line: %s %s" % (RDPM_PATH, argStr))
        sys.exit(0)
    output = execute(RDPM_PATH, argStr)

    #
    # Parse output and reduce verbosity
    #
    result = re.findall(r"Programming IDAU(.*?)SUCCESSFUL!", output, re.MULTILINE|re.DOTALL)
    if result:
        print("Programming IDAU" + result[0] + "SUCCESSFUL!")
    else:
        print(output)


if __name__ == "__main__":
    main()
