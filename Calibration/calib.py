import cv2 as cv, numpy as np, glob, json, os, sys

# --- Board definition (yours) ---
SQUARE = 0.050   # meters
MARKER = 0.037   # meters
SX, SY = 16, 11  # squaresX, squaresY (columns, rows)

def make_board(dict_id):
    adict = cv.aruco.getPredefinedDictionary(dict_id)
    return adict, cv.aruco.CharucoBoard((SX, SY), SQUARE, MARKER, adict)

# Try the common 7x7 dictionaries
DICT_CANDIDATES = [cv.aruco.DICT_7X7_1000, cv.aruco.DICT_7X7_250]

def detect_charuco(gray):
    for d in DICT_CANDIDATES:
        adict, _board = make_board(d)
        corners, ids, _ = cv.aruco.detectMarkers(gray, adict)
        if ids is None or len(ids) < 8: continue
        ret, ch_corners, ch_ids = cv.aruco.interpolateCornersCharuco(corners, ids, gray, _board)
        if ret and ch_ids is not None and len(ch_ids) >= 15:
            return d, ch_corners, ch_ids
    return None, None, None

# Collect detections
all_charuco = []  # per image: (dict_id, ch_corners, ch_ids)
img_size = None
img_files = sorted(glob.glob("cam0_imgs/*.png"))
if not os.path.isdir("cam0_imgs") or len(img_files) == 0:
    print("No input images found in 'cam0_imgs/'. Place PNG images of the Charuco board there and re-run.")
    # show a small hint about other image locations in the workspace
    sample_paths = [p for p in glob.glob("../**/*.png", recursive=True)[:5]]
    if sample_paths:
        print("Some other PNGs found nearby (not used):")
        for p in sample_paths:
            print("  ", p)
    sys.exit(1)

for fn in img_files:
    img = cv.imread(fn)
    if img_size is None: img_size = img.shape[1], img.shape[0]
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    d, ch_c, ch_ids = detect_charuco(gray)
    if d is not None:
        all_charuco.append((d, ch_c, ch_ids))

# Pick the dictionary that appeared most often
from collections import Counter
if not all_charuco:
    print("No Charuco detections were found in the provided images. Ensure the board is visible and try more images.")
    sys.exit(1)

picked = Counter([d for d,_,_ in all_charuco]).most_common(1)[0][0]
adict, board = make_board(picked)

# Re-run interpolation with the picked dict to gather all samples
ch_corners_list, ch_ids_list = [], []
for fn in sorted(glob.glob("cam0_imgs/*.png")):
    gray = cv.cvtColor(cv.imread(fn), cv.COLOR_BGR2GRAY)
    corners, ids, _ = cv.aruco.detectMarkers(gray, adict)
    if ids is None: continue
    ret, ch_c, ch_ids = cv.aruco.interpolateCornersCharuco(corners, ids, gray, board)
    if ret and ch_ids is not None and len(ch_ids) >= 15:
        ch_corners_list.append(ch_c)
        ch_ids_list.append(ch_ids)

flags = (cv.CALIB_RATIONAL_MODEL | cv.CALIB_FIX_K3)  # good starting flags
ret, K, dist, rvecs, tvecs = cv.aruco.calibrateCameraCharuco(
    charucoCorners=ch_corners_list,
    charucoIds=ch_ids_list,
    board=board,
    imageSize=img_size,
    cameraMatrix=None,
    distCoeffs=None,
    flags=flags)

print("Reprojection error (px):", ret)
json.dump({"K": K.tolist(), "dist": dist.squeeze().tolist(),
           "dict": int(picked), "SX": SX, "SY": SY,
           "square_m": SQUARE, "marker_m": MARKER},
          open("cam0_intrinsics.json","w"), indent=2)
