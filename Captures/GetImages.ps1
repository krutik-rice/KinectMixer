Get-ChildItem *.mkv | ForEach-Object {
    $baseName = "$($_.DirectoryName)\$($_.BaseName)"

    # Extract 3 frames from the first second (adjust -vsync/-vf if needed)
    for ($i = 0; $i -lt 1; $i++) {
        $out = "$baseName-$i.png"
        $count = 1

        # If file exists, increment
        while (Test-Path $out) {
            $out = "$baseName-$i-$count.png"
            $count++
        }

        # Grab the frame at timestamp = i seconds
        ffmpeg -ss 00:00:$i -i $_.FullName -frames:v 3 "$out"
    }
}


# Delete MKVs after extraction
Get-ChildItem *.mkv | Remove-Item -Force

Get-ChildItem *.png | ForEach-Object {
    $fileName = $_.BaseName
    $ext = $_.Extension
    $dir = $_.DirectoryName

    if ($fileName -match "^(.*?)-") {
        $prefix = $matches[1]
        $targetDir = Join-Path $dir $prefix

        # Create folder if it doesn't exist
        if (!(Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir | Out-Null
        }

        # Build initial destination path
        $dest = Join-Path $targetDir ($_.Name)
        $count = 1

        # If file exists, append -1, -2, etc.
        while (Test-Path $dest) {
            $dest = Join-Path $targetDir ("$fileName-$count$ext")
            $count++
        }

        # Move file to unique destination
        Move-Item $_.FullName -Destination $dest
    }
}
