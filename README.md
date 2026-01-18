# GoGo Board 7 Firmware Installer

This is a web-based firmware installer for the GoGo Board 7. It allows users to easily flash the latest firmware to their devices directly from the browser using Web Serial API.

**Use the Web Installer: [https://install-firmware.gogoboard.org](https://install-firmware.gogoboard.org)**

## Features

-   **Easy Installation**: Connect your device and click "Install".
-   **Multiple Versions**: Support for stable releases and pre-release previews.
-   **Automatic Manifest Generation**: Python script to fetch the latest firmware assets from GitHub.


## Project Structure

-   `index.html`: The main web interface.
-   `gen_manifest.py`: Script to fetch firmware and generate manifests.
-   `manifests.json`: Configuration file listing available firmware versions.
-   `firmware/`: Directory storing downloaded firmware binaries.
-   `manifest/`: Directory storing generated manifest JSON files.
-   `assets/`: Images and other static assets.
-   `js/`: JavaScript helper files.

## License

[MIT License](LICENSE)
