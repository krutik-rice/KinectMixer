#!/bin/bash


start cmd.exe /c k4arecorder --device 0 --color-mode 720p --external-sync master -l 10 Recordings/mas.mkv
start cmd.exe /c k4arecorder --device 1 --color-mode 720p --external-sync subordinate -l 10 Recordings/sub1.mkv 
start cmd.exe /c k4arecorder --device 2 --color-mode 720p --external-sync subordinate -l 10 Recordings/sub2.mkv 

