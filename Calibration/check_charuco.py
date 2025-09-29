#!/usr/bin/env python3
import argparse, os, glob, sys, time
import numpy as np
import cv2 as cv

# ---------- Board defaults (your PDF) ----------
DEFAULT_SX, DEFAULT_SY = 16, 11         # squaresX, squaresY
DEFAULT_SQUARE = 0.050                  # meters
DEFAULT_MARKER = 0.037                  # meters
DICT_CANDIDATES = [cv.aruco.DICT_7X7_1000, cv.aruco.DICT_7X7_250]

def make_board(sx, sy, square_m, marker_m, dict_id):
    ad = cv.aruco.getPredefinedDictionary(dict_id)
    board = cv.aruco.CharucoBoard((sx, sy), square_m, marker_m, ad)
    return ad, board

def detect_charuco(gray, sx, sy, square_m, marker_m, try_auto_dict=True, fixed_dict=None):
    dicts = [fixed_dict] if fixed_dict is not None else DICT_CANDIDATES
    for d in dicts:
        ad, board = make_board(sx, sy, square_m, marker_m, d)
        corners, ids, _ = cv.aruco.detectMarkers(gray, ad)
        if ids is None or len(ids) == 0:
            continue
        # Refine & interpolate ChArUco corners
        ret, ch_corners, ch_ids = cv.aruco.interpolateCornersCharuco(
            corners, ids, gray, board)
        if ret and ch_ids is not None and len(ch_ids) >= 8:
            return d, ad, board, corners, ids, ch_corners, ch_ids
    return None, None, None, None, None, None, None

def solve_pose_charuco(gray, K=None, dist=None, sx=DEFAULT_SX, sy=DEFAULT_SY,
                       square_m=DEFAULT_SQUARE, marker_m=DEFAULT_MARKER, dict_id=None):
    d, ad, board, corners, ids, ch_c, ch_ids = detect_charuco(
        gray, sx, sy, square_m, marker_m,
        try_auto_dict=(dict_id is None),
        fixed_dict=dict_id
    )
    result = {
        "ok": False, "used_dict": None, "num_markers": 0, "num_charuco": 0,
        "rvec": None, "tvec": None, "reproj_error_px": None,
        "corners": None, "ids": None, "charuco_corners": None, "charuco_ids": None,
        "board": None, "aruco_dict": None
    }
    if d is None:
        return result

    result["used_dict"] = int(d)
    result["aruco_dict"] = ad
    result["board"] = board
    result["corners"] = corners
    result["ids"] = ids
    result["charuco_corners"] = ch_c
    result["charuco_ids"] = ch_ids
    result["num_markers"] = len(ids) if ids is not None else 0
    result["num_charuco"] = len(ch_ids) if ch_ids is not None else 0

    if K is None or dist is None:
        # Try a pose anyway (OpenCV requires intrinsics for Charuco pose).
        # If none provided, we can't compute a metric pose; return detection only.
        return result

    ok, rvec, tvec = cv.aruco.estimatePoseCharucoBoard(ch_c, ch_ids, board, K, dist, None, None)
    if not ok:
        return result

    result["ok"] = True
    result["rvec"] = rvec
    result["tvec"] = tvec

    # Compute reprojection error (only over the detected Charuco corners)
    # Get corresponding 3D board corner points for each charuco id:
    # CharucoBoard in OpenCV exposes `chessboardCorners` as Nx3 array (float32)
    obj3d = board.chessboardCorners  # (N, 3)
    used_ids = ch_ids.flatten().astype(int)
    objp = obj3d[used_ids]  # (M, 3) in board coordinate frame

    imgpts, _ = cv.projectPoints(objp, rvec, tvec, K, dist)
    imgpts = imgpts.reshape(-1, 2)
    obs = ch_c.reshape(-1, 2)
    err = np.linalg.norm(imgpts - obs, axis=1)
    result["reproj_error_px"] = float(np.mean(err))
    return result

def draw_overlay(img, res, K=None, dist=None, axis_len=0.15):
    out = img.copy()
    if res["corners"] is not None and res["ids"] is not None:
        cv.aruco.drawDetectedMarkers(out, res["corners"], res["ids"])
    if res["charuco_corners"] is not None and res["charuco_ids"] is not None:
        cv.aruco.drawDetectedCornersCharuco(out, res["charuco_corners"], res["charuco_ids"], (0,255,0))
    if res["ok"] and K is not None and dist is not None:
        cv.drawFrameAxes(out, K, dist, res["rvec"], res["tvec"], axis_len)  # draws X(red), Y(green), Z(blue)
    return out

def load_calib(json_path):
    import json
    data = json.load(open(json_path, "r"))
    K = np.array(data["K"], dtype=np.float64)
    dist = np.array(data["dist"], dtype=np.float64).reshape(-1, 1)
    return K, dist

def process_image(path, K, dist, args):
    img = cv.imread(path)
    if img is None:
        print(f"[WARN] Could not read {path}")
        return False
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    res = solve_pose_charuco(
        gray,
        K=K, dist=dist,
        sx=args.sx, sy=args.sy,
        square_m=args.square, marker_m=args.marker,
        dict_id=args.force_dict
    )
    disp = draw_overlay(img, res, K, dist)
    ok = res["ok"]
    msg = (
        f"{os.path.basename(path)} | dict={res['used_dict']} "
        f"| markers={res['num_markers']}, charuco={res['num_charuco']} "
        f"| pose={'OK' if ok else 'FAIL'}"
    )
    if res["reproj_error_px"] is not None:
        msg += f", reproj_err={res['reproj_error_px']:.3f}px"
    print(msg)

    if args.show:
        # Create a resizable window so the user can freely resize the display
        cv.namedWindow("ChArUco Check", cv.WINDOW_NORMAL)
        cv.imshow("ChArUco Check", disp)
        key = cv.waitKey(0 if not args.autoadvance else args.delay)
        if key == 27:  # ESC
            cv.destroyAllWindows()
            sys.exit(0)

    if args.save is not None:
        os.makedirs(args.save, exist_ok=True)
        out_path = os.path.join(args.save, os.path.basename(path))
        cv.imwrite(out_path, disp)

    # Simple pass/fail heuristic
    if res["num_charuco"] >= args.min_charuco and ok and \
       (res["reproj_error_px"] is None or res["reproj_error_px"] <= args.max_err):
        return True
    return False

def run_webcam(cam_index, K, dist, args):
    cap = cv.VideoCapture(cam_index)
    if not cap.isOpened():
        print(f"[ERR] Cannot open camera index {cam_index}")
        return
    print("[INFO] Press 'q' to quit, 's' to save frame overlay.")
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        res = solve_pose_charuco(
            gray, K=K, dist=dist,
            sx=args.sx, sy=args.sy,
            square_m=args.square, marker_m=args.marker,
            dict_id=args.force_dict
        )
        disp = draw_overlay(frame, res, K, dist)
        txt = f"markers={res['num_markers']}  charuco={res['num_charuco']}  "
        if res["reproj_error_px"] is not None:
            txt += f"err={res['reproj_error_px']:.2f}px  "
        txt += f"pose={'OK' if res['ok'] else '...'}"
        cv.putText(disp, txt, (12, 28), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 3, cv.LINE_AA)
        cv.putText(disp, txt, (12, 28), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1, cv.LINE_AA)
        # Ensure the live window is resizable so users can scale it as desired
        # Create the window once (idempotent): namedWindow can be called repeatedly.
        cv.namedWindow("ChArUco Live Check", cv.WINDOW_NORMAL)
        cv.imshow("ChArUco Live Check", disp)
        k = cv.waitKey(1) & 0xFF
        if k == ord('q') or k == 27:
            break
        if k == ord('s') and args.save is not None:
            os.makedirs(args.save, exist_ok=True)
            out_path = os.path.join(args.save, f"webcam_{saved:04d}.png")
            cv.imwrite(out_path, disp)
            saved += 1
    cap.release()
    cv.destroyAllWindows()

def parse_args():
    p = argparse.ArgumentParser(
        description="ChArUco board checker: detects, solves pose, and reports reprojection error."
    )
    p.add_argument("--images", help="Glob pattern or folder with images (e.g., 'imgs/*.png' or 'imgs')", default=None)
    p.add_argument("--webcam", type=int, help="Webcam index (0 default). Uses provided intrinsics.", default=None)
    p.add_argument("--calib", help="Path to intrinsics JSON (with fields K and dist).", required=False)
    p.add_argument("--sx", type=int, default=DEFAULT_SX, help="squaresX (default 16)")
    p.add_argument("--sy", type=int, default=DEFAULT_SY, help="squaresY (default 11)")
    p.add_argument("--square", type=float, default=DEFAULT_SQUARE, help="squareLength in meters (default 0.050)")
    p.add_argument("--marker", type=float, default=DEFAULT_MARKER, help="markerLength in meters (default 0.037)")
    p.add_argument("--force-dict", type=int, default=None,
                   help="Force an ArUco dictionary id (e.g., 18 for DICT_7X7_1000). If omitted, will try a couple automatically.")
    p.add_argument("--show", action="store_true", help="Show overlay windows")
    p.add_argument("--autoadvance", action="store_true", help="Auto-advance images when showing")
    p.add_argument("--delay", type=int, default=500, help="Delay in ms for auto-advance")
    p.add_argument("--save", help="Folder to save overlaid outputs", default=None)
    p.add_argument("--min-charuco", type=int, default=15, help="Minimum detected ChArUco corners to consider OK")
    p.add_argument("--max-err", type=float, default=0.80, help="Max mean reprojection error (px) to consider OK")
    return p.parse_args()

def main():
    args = parse_args()
    K = dist = None
    if args.calib:
        K, dist = load_calib(args.calib)
        print("[INFO] Loaded intrinsics from", args.calib)
    else:
        print("[WARN] No intrinsics provided. Pose and reprojection error will be unavailable.")

    # Webcam mode
    if args.webcam is not None:
        run_webcam(args.webcam, K, dist, args)
        return

    # Images mode
    if args.images is None:
        print("[ERR] Provide --images pattern/folder or --webcam index")
        sys.exit(2)

    pattern = args.images
    if os.path.isdir(pattern):
        pattern = os.path.join(pattern, "*.*")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"[ERR] No images matched: {args.images}")
        sys.exit(3)

    ok_count = 0
    for f in files:
        ok = process_image(f, K, dist, args)
        ok_count += int(ok)

    print(f"[SUMMARY] {ok_count}/{len(files)} passed thresholds "
          f"(min_charuco={args.min_charuco}, max_err={args.max_err}px).")

if __name__ == "__main__":
    main()
