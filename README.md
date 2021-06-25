# idautool

Tool to extract and set IDAU boundary registers for Renesas RA6M5 MCUs


## Prerequsites

Renesas' e2Studio must be installed as it provides the `RenesasDevicePartitionManagerCmd` tool.


## How it works

The *idautool* parses a compiled ELF file and extracts from the symbol table the location of the IDAU partitions and calculates the size of each partition.
Then it composes a command line with arguments for the `RenesasDevicePartitionManagerCmd` which is utilised to set the partition boundary registers of the Renesas RA MCU.

The default programmer is J-link, but e2 and e2 Lite can be used as well (`--emuType` command line option).


## Usage

```
python idautool.py --help
```
```
Set IDAU boundary registers for Renesas RA6M5 MCUs
Usage: idautool.py ELFFILE

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         verbose mode
  -e EMUTYPE, --emuType=EMUTYPE
                        emulator type (jlink, e2 or e2lite)
```


Sample run:


```
python idautool.py quickstart_ek_ra6m5_ep.elf
```
```
Set IDAU boundary registers for Renesas RA6M5 MCUs
Execute: c:\Users\...\.eclipse\com.renesas.platform_1476787444\DebugComp\RA\DevicePartitionManager\RenesasDevicePartitionManagerCmd.exe -emuType jlink -action BOUNDARY -idauCFS 11 -idauCFNSC 21 -idauDFS 0 -idauSRAMS 15 -idauSRAMNSC 1
Programming IDAU memory boundaries with the following region size settings...
        -       Code Flash Secure       (kB)    : 11
        -       Code Flash NSC          (kB)    : 21
        -       Data Flash Secure       (kB)    : 0
        -       SRAM Secure             (kB)    : 15
        -       SRAM NSC                (kB)    : 1
SUCCESSFUL!
```


## Potential issues

The install location of the `RenesasDevicePartitionManagerCmd` tool is currently hardcoded as `RDPM_PATH`.  This may need adjustment depending on the e2Studio version.
