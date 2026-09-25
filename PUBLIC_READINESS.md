# Public source and privacy

This repository starts from a reviewed source-only snapshot with fresh Git
history. It does not include development history, local backups, configured
firmware dumps, account credentials, usage databases, or personal reference photos.

The pre-publication scan checked tracked content for known personal identifiers,
private deployment settings, account-specific readings, and credential patterns.
No matches were found. Pattern scans are not a guarantee against every possible
secret format. Commit attribution uses the public GitHub handle Safken and a
GitHub noreply address.

The original `case/stl/Screen holder-v6.stl` is included byte-for-byte; its checksum
is recorded in the assembly guide. Software and project-authored documentation
use MIT, the model uses CC BY-NC 4.0, and Manrope retains SIL OFL.

## Reproducing the project

Start with [INSTALL.md](INSTALL.md), the [materials list](BOM.md), and the
[print and assembly guide](case/README.md). The GitHub Actions workflow tests
Windows/Linux software and builds release/demo firmware from pinned dependencies.
See [VALIDATION.md](VALIDATION.md) for tested behavior and remaining limitations.
The [MakerWorld listing](https://makerworld.com/en/models/3353225-codex-usage-monitor-under-monitor-screen-holder#profileId-3811349) is published with a print profile. Exact settings
for the original fit-tested print were not recorded beyond P1S, PLA, and a
0.4 mm nozzle. The live MakerWorld listing was verified to use CC BY-NC 4.0,
matching the model license in this repository.

## Keep local data private

Account credentials stay on the Ubuntu server and Wi-Fi credentials stay on the
screen. Local configuration, databases, logs, and build directories are ignored
by Git. The dashboard is a read-only, unauthenticated trusted-LAN service;
do not expose it to the public Internet. Use your own network settings and account.

Publish only reviewed source and clean build artifacts. Never upload configured
flash dumps, auth files, usage databases, or local history backups. Use synthetic
demo readings or a powered-off screen and a neutral background for public photos.
