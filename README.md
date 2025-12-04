# SC Merits Calc
## A Star Citizen prison calculator

![Preview](https://github.com/PINKgeekPDX/SCMeritsCalc/blob/main/preview/image.png)

A Windows desktop app built with Python and PyQt6 for calculating Star Citizen prison merits, sentence time, and aUEC conversions.

## Features

  - Convert between Merits and Prison Sentence Time (default 1 Merit = 1 Second).
  - Convert between Merits and aUEC (default rate 61.8%, adjustable).
  - Customize keyboard shortcuts.
  - Enter Merits to see time reduction and aUEC value.
  - Enter Time (HH:MM:SS) to see required Merits and cost.
  - Enter aUEC to see how many Merits you can buy/sell.
  - Adjust conversion rates and fees.
  - Customize rates if the economy changes.
  - Generate text reports of your calculations and save to file or clipboard.
  ----------------------------------------
  - Default Merit Rate: 1 Merit = 1 Second
  - Default aUEC Rate: 0.618 (61.8%)
  - Default Opacity: 0.9
  - Default Shortcuts: Ctrl+S Save, Ctrl+Q Quit

## Installation

RECOMMENDED OPTION (MeritsCalc-Setup.exe):
Download and run the installer from the [Releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases) page.

-----

OPTION 2 (MeritsCalc.exe):
If you already have dependencies on PC you can use the standalone .exe from the [Releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases) page.

------

OPTION 3 (scripts/build-exe.ps1):
If you prefer to build from source or run it from source, see below.

## -------------------------------------------------

## Run from source

1. Ensure Python 3.11+ is installed.

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python -m meritscalc.main
```

## -------------------------------------------------

## Build from source

EXE build:

```powershell
./scripts/build_exe.ps1
```

Installer build (requires Inno Setup):

```powershell
./scripts/build_installer.ps1
```

## -------------------------------------------------

## Tests

Run Windows-targeted tests for DPI, persistence, and transparency input:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Project links:

- Repo: [https://github.com/PINKgeekPDX/SCMeritsCalc](https://github.com/PINKgeekPDX/SCMeritsCalc)
- Releases: [https://github.com/PINKgeekPDX/SCMeritsCalc/releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases)
- Issues: [https://github.com/PINKgeekPDX/SCMeritsCalc/issues](https://github.com/PINKgeekPDX/SCMeritsCalc/issues)



## License

Open Source
MIT
