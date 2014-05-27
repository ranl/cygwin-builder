cygwin-builder
==============

Generate windows installer for cygwin


Build Machine Requirements
==========================
 - Python 2.6 or 2.7
 - An internet connection to one of the mirrors in https://cygwin.com/mirrors.lst
 - NSIS >= 3.0 - http://nsis.sourceforge.net
 - no requirements needed on the destination machine


Examples
========

```
git clone https://github.com/ranl/cygwin-builder.git
cd cygwin-builder
c:\python27\python.exe build.py --help
c:\python27\python.exe build.py build.json
```

### build.json

```json
{
    "mirror": "http://mirror.isoc.org.il/pub/cygwin/",
    "packages": [
        "unzip",
    ]
}
```

### build.json - override defaults
```json
{
    "installer": "http://cygwin.com/setup-x86_64.exe",
    "makensis": "c:\\Program Files (x86)\\NSIS\\makensis.exe",
    "mirror": "http://mirror.isoc.org.il/pub/cygwin/",
    "packages": [
        "openssh",
        "zip",
        "vim",
        "wget",
        "rsync",
        "curl",
        "unzip",
        "cygrunsrv",
        "dos2unix"
    ]
}
```

