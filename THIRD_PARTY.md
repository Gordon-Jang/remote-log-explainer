# Third-party components

## Microsoft Sysinternals Handle

Remote Log Explainer can use Microsoft Sysinternals **Handle** to identify processes that hold open handles to directories or files.

- Upstream: https://learn.microsoft.com/sysinternals/downloads/handle
- Download used by the installer: https://download.sysinternals.com/files/Handle.zip
- Publisher verification: the installer requires a valid Authenticode signature whose signer contains `Microsoft Corporation`.
- The executable is downloaded at install time into `%USERPROFILE%\.remote-log-explainer\tools\handle64.exe`.
- The Git repository does **not** redistribute `handle64.exe`.
- The downloaded `Eula.txt` is copied beside the tool as `Handle-Eula.txt`.

Sysinternals Handle is Microsoft software and is **not** covered by this repository's MIT License.
