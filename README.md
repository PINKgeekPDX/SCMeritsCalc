#

# // **S.C.M.C** // Star Citizen Merits Calculator //

# [http://www.scmc.space](http://www.scmc.space)

![License](https://img.shields.io/github/license/PINKgeekPDX/SCMeritsCalc?style=for-the-badge)
![Release](https://img.shields.io/github/v/release/PINKgeekPDX/SCMeritsCalc?style=for-the-badge)
![Downloads](https://img.shields.io/github/downloads/PINKgeekPDX/SCMeritsCalc/total?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)

## ==| Purpose |==

> **A Star Citizen prison calculator:**

- A Windows desktop app for calculating Star Citizen prison merits, sentence time, and aUEC conversions.
- Regularly updated and maintained.

## ==| Screenshots |==

<div align="center">
  <a href="https://github.com/PINKgeekPDX/SCMeritsCalc/blob/main/preview/image0.png"><img src="https://raw.githubusercontent.com/PINKgeekPDX/SCMeritsCalc/main/preview/image0.png" width="45%" alt="Calculator"></a>......
  <a href="https://github.com/PINKgeekPDX/SCMeritsCalc/blob/main/preview/image1.png"><img src="https://raw.githubusercontent.com/PINKgeekPDX/SCMeritsCalc/main/preview/image1.png" width="45%" alt="Settings"></a>
  <br><br>
  <a href="https://github.com/PINKgeekPDX/SCMeritsCalc/blob/main/preview/image2.png"><img src="https://raw.githubusercontent.com/PINKgeekPDX/SCMeritsCalc/main/preview/image2.png" width="45%" alt="Help"></a>......
  <a href="https://github.com/PINKgeekPDX/SCMeritsCalc/blob/main/preview/image3.png"><img src="https://raw.githubusercontent.com/PINKgeekPDX/SCMeritsCalc/main/preview/image3.png" width="45%" alt="About"></a>
</div>

## ==| Features |==

> **Calculations:**

- Convert between Merits and Prison Sentence Time (default 1 Merit = 1 Second).
- Convert between Merits and aUEC (default rate 61.8%, adjustable).
- Enter Merits to see time reduction and aUEC value.
- Enter Time (HH:MM:SS) to see required Merits and cost.
- Enter aUEC to see how many Merits you can buy/sell.
- Generate text reports of your calculations (Save to file or Clipboard).

> **Settings:**

- Adjust conversion rates and fees to match the economy.
- 'Always on Top' window option.
- Transparency opacity slider.
- System Tray integration (minimize to tray).
- Auto-update check for downloading and installing updates automatically.

## ==| Installation Options |==

> **OPTION ( 1 )**

- **Windows 10/11 Installer -** SCMC_Installer.exe:
  - If you just want to use the app and get it running the easiest way possible, download and run the installer from the [Releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases) page.

> **OPTION ( 2 )**

- **Standalone .exe ( may requires dependencies ) -** SCMC.exe:
  - If you already have dependencies on PC you can use the standalone .exe from the [Releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases) page.

> **OPTION ( 3 )**

- **Build App .EXE From Source -** build_exe.ps1:
  - If you prefer to build the standalone .exe from source.
  - ( Optional ) Authenticode signing (recommended for SmartScreen):
    - Requires a Windows code-signing certificate + Windows SDK (signtool.exe).
    - Configure one of:
      - **SCMC_SIGN_THUMBPRINT** = cert thumbprint from Windows Cert Store
      - **SCMC_SIGN_PFX_PATH** = path to a `.pfx` code-signing cert
    - Optional:
      - **SCMC_SIGN_PFX_PASSWORD** = password for the `.pfx`
      - **SCMC_SIGN_TIMESTAMP_URL** = timestamp server (default: `http://timestamp.digicert.com`)
    - Use **-Sign** to _require_ signing (script will fail if no cert is configured).

```powershell
./scripts/build_exe.ps1
./scripts/build_exe.ps1 -Sign
```

> **OPTION ( 4 )**

- **Build Installer ( may require Inno setup ) -** build_installer.ps1:
  - If you prefer to build the installer .exe from source.
  - ( Optional ) Authenticode signing uses the same `SCMC_SIGN_*` variables as above.
  - Note: build_installer expects `dist\\SCMC.exe` to exist first (build_exe.ps1 produces and can sign it).

```powershell
./scripts/build_installer.ps1
./scripts/build_installer.ps1 -Sign
```

> **OPTION ( 5 )**

- **Run from Source -** Steps:

  - Ensure Python 3.11+ is installed.
  - Install dependencies using: **pip install -r requirements.txt**
  - Run the application using: **python -m meritscalc.main**

## ==| Project links |==

> **PROJECT REPO**:

- [https://github.com/PINKgeekPDX/SCMeritsCalc](https://github.com/PINKgeekPDX/SCMeritsCalc)

> **REPORT ISSUES**:

- [https://github.com/PINKgeekPDX/SCMeritsCalc/issues](https://github.com/PINKgeekPDX/SCMeritsCalc/issues)

> **DOWNLOAD RELEASES**:

- [https://github.com/PINKgeekPDX/SCMeritsCalc/releases](https://github.com/PINKgeekPDX/SCMeritsCalc/releases)

## ==| Disclaimer |==

> - This is an unofficial, third-party application not affiliated with Cloud Imperium Games (CIG) or Roberts Space Industries.

> - SCMC strictly adheres to all third-party tool guidelines and does not violate the CIG Terms of Service or End User License Agreement in any way.

> - Use of this tool is at your own risk. "PINKgeekPDX" is not endorsed by or connected with CIG or any of its subsidiaries.

## ==| MIT License |==

> // Copyright (c) 2025 **PINKgeekPDX** //

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
