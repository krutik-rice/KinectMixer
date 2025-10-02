
## KinectMixer — capture helper for multi-Kinect workflows

This repository contains small scripts and helpers to capture video and extract images from Azure Kinect (or similar) recordings. The main goal is to produce recorded videos and image sequences suitable for later 3D reconstruction and calibration.

Note: the instructions below assume a Windows environment (PowerShell, .bat files). If you use another platform, adapt the commands accordingly.

## Quick checklist (what this README covers)
- Prerequisites
- How to record video
- How to capture image sequences from MKV files
- Running image-extraction (`GetImages.ps1`)
- Calibration utilities
- Folder layout and tips

## Prerequisites
- Windows 10/11 with PowerShell (the repo includes .bat and .ps1 scripts). 
- Azure Kinect SDK or compatible Kinect driver (assumed; replace with your device driver if different).
- FFmpeg available in PATH (required by `GetImages.ps1` and other extraction steps).
- Python 3.8+ and OpenCV if you plan to run the scripts in `Calibration/` (e.g. `calib.py`).

If you don't have FFmpeg installed, download it from https://ffmpeg.org/ and add the `bin` folder to your PATH.

## Typical workflow

1. Record video from the Kinect(s) using `Record_video.bat`.
2. Optionally record images (or recording MKV) using `Capture_image.bat`.
3. Convert MKV recordings to image sequences and sort them into per-device folders using `GetImages.ps1`.
4. Run the calibration scripts in `Calibration/` to compute intrinsics/extrinsics.

## Usage

Recording (example)

Run the batch to start a recording session. The actual behavior depends on the batch implementation and connected device.

PowerShell / Command Prompt (run from the repo root):

```
Record_video.bat
```

Capture images / MKV (example)

```
Capture_image.bat
```

Extract images from recordings and organize

`GetImages.ps1` will extract frames from .mkv files using FFmpeg, place them into device folders, and delete the .mkv to free space. Run it from the `Captures` folder or pass the path to the folder containing .mkv files.

Example (PowerShell):

```
cd .\Captures
.\\GetImages.ps1
```

If you prefer to run it from anywhere, open the script and change the folder variables, or call it with a path argument (if implemented).

## Calibration

The `Calibration/` folder contains helper scripts for Charuco/Chessboard-based calibration:
- `calib.py` — main calibration tool (Python + OpenCV assumed)
- `check_charuco.py` — utilities to visualize or check Charuco detections
- `sample_frames/` — example images used for testing the calibration scripts

Typical steps:
1. Collect synchronized image sets from each sensor and put them under `Captures/<device>/`.
2. Use `GetImages.ps1` to extract frames if you recorded MKVs.
3. Run `Calibration/calib.py` with the folder that contains the images for each camera.

Refer to the comments inside each script for specific command-line flags and expected image naming conventions.

## Folder layout

- `Calibration/` — calibration scripts and samples
- `Captures/` — recorded mkv files and device folders (contains `GetImages.ps1`)
- `Recordings/` — example or completed recordings (mkvs)
- `Record_video.bat`, `Capture_image.bat` — helper scripts to start recordings
- `k4a.ps1` — (helper PowerShell script — likely for Azure Kinect)

## Troubleshooting
- "FFmpeg not found": ensure ffmpeg is installed and `ffmpeg.exe` is reachable from PowerShell (add to PATH).
- "Device not found / driver error": confirm Azure Kinect SDK is installed and the device shows up (check Device Manager).
- If images look unsynchronized across cameras, verify trigger and timestamps, and re-check capture settings.

## Small tips
- Keep large recordings on a fast drive (NVMe or SSD) to avoid dropped frames.
- Delete or move large .mkv files after extracting frames to save space — `GetImages.ps1` already deletes mkvs by default.

## Contributing / Next steps
- If you want, add a small example of your device configuration or a sample command-line flag list for `Record_video.bat` and `Capture_image.bat`.

## License & Contact
This repo doesn't include an explicit license file. However, a message saying this repo was helpful will boost my mood. :D
