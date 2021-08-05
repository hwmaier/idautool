# idautool

Tool to extract and set IDAU boundary registers for Renesas RA TrustZone MCUs


## Prerequsites

Renesas Flash Programmer v3 must be installed as it provides the `rfp-cli` tool.
Currently only Windows is supported.


## How it works

The *idautool* parses a compiled ELF file and extracts from the symbol table the location of the IDAU partitions and calculates the size of each partition.
Then it composes a command line with arguments for the `rfp-cli` which is utilised to set the partition boundary registers of the Renesas RA MCU.

The default programmer is J-link, but e2 and e2 Lite can be used as well (`--tool` command line option).

The tool checks first current setting and only re-programs when the new settings are different. This avoids repetitive flashing of identical settings during debug sessions.


## Usage

```
python idautool.py --help
```
```
Set IDAU boundary registers for Renesas RA TrustZone MCUs
Usage: idautool.py ELFFILE

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         verbose mode
  -t TOOL, --tool=TOOL  programming tool (jlink, e2 or e2l)
  -d, --dryrun          dry run, don't change anything, print command line only
```


Sample run:


```
python idautool.py quickstart_ek_ra6m5_ep.elf
```
```
Set IDAU boundary registers for Renesas RA TrustZone MCUs
IDAU boundary registers are different, re-programming...
Renesas Flash Programmer CLI V1.01
Module Version: V3.08.02.000
Connecting the tool (J-Link)
Tool: J-Link (SEGGER J-Link ARM)
Interface: 2 wire UART
Connecting the target device
Speed: 115,200 bps
Connected to R7FA6M5BH3CFC
Writing data to the target device
  [Flash Options]
    Boundary
Disconnecting the tool
Operation successful
```
