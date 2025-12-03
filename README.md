# SC Merits Calc — Star Citizen Prison Calculator

![Preview](https://github.com/PINKgeekPDX/SCMeritsCalc/blob/main/preview/image.png)

A Windows desktop app built with Python and PyQt6 for calculating Star Citizen prison merits, sentence time, and aUEC conversions.

## Features

- **Merit Calculations**: Convert between Merits and Prison Sentence Time (default 1 Merit = 1 Second).
- **Economic Conversion**: Convert between Merits and aUEC (default rate 61.8%, adjustable).
- **Bidirectional Updates**: Typing in any field automatically updates the others.
- **Additional**:
  - Adjust conversion rates and fees.
  - Customize keyboard shortcuts.
- **Reports**: Generate text reports of your calculations and save to file or clipboard.

## Installation

Download and run the installer (MeritsCalc-Setup.exe) from the [Releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases) page.

1. Ensure Python 3.11+ is installed.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Project links:

- Repo: [https://github.com/PINKgeekPDX/SCMeritsCalc](https://github.com/PINKgeekPDX/SCMeritsCalc)
- Issues: [https://github.com/PINKgeekPDX/SCMeritsCalc/issues](https://github.com/PINKgeekPDX/SCMeritsCalc/issues)

## Usage

1. Run the application:

```bash
python -m meritscalc.main
```

1. Calculator Tab:
   - Enter Merits to see time reduction and aUEC value.
   - Enter Time (HH:MM:SS) to see required Merits and cost.
   - Enter aUEC to see how many Merits you can buy/sell.
1. Settings Tab:
   - Customize rates if the economy changes.
   - Toggle aspect ratio enforcement.
   - Enable snapping to screen edges or other app windows.
   - Adjust transparency and customize keyboard shortcuts.

## Build

EXE build:

```powershell
./scripts/build_exe.ps1
```

Installer build (requires Inno Setup):

```powershell
./scripts/build_installer.ps1
```

Releases:

- [https://github.com/PINKgeekPDX/SCMeritsCalc/releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases)

## Configuration

Settings and logs are saved in the user's Documents directory:

- `Users/<user>/Documents/PINK/SCMeritCalc/settings.json`
- `Users/<user>/Documents/PINK/SCMeritCalc/ScMeritCalc.log` (appends at startup)

- Default Merit Rate: 1 Merit = 1 Second
- Default aUEC Rate: 0.618 (61.8%)
- Default Opacity: 0.9
- Default Shortcuts: Ctrl+S Save, Ctrl+Q Quit

## Tests

Run Windows-targeted tests for DPI, persistence, and transparency input:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## License

Open Source

MIT
