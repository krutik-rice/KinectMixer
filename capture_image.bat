#!/bin/bash


start cmd.exe /c k4arecorder --device 1 --color-mode 2160p  --external-sync subordinate -l 4 Captures/sub1.mkv
start cmd.exe /c k4arecorder --device 2 --color-mode 2160p  --external-sync subordinate -l 4 Captures/sub2.mkv
start cmd.exe /c k4arecorder --device 0 --color-mode 2160p  --external-sync master -l 4 Captures/mas.mkv






