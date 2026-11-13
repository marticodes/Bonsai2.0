import base64

import cv2


def _screenshot_filename(index: int, timestamp: float) -> str:
    minutes = int(timestamp // 60)
    seconds = timestamp % 60
    return f"screenshot_{index:04d}_t{minutes:02d}m{seconds:05.2f}s.jpg"


def extract_frames(
    video_path: str,
    interval_seconds: int = 5,
) -> dict:
    """
    Extract one frame every interval_seconds from a video.

    Returns video metadata and Base64-encoded JPEG frames.
    """

    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than zero")

    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        raise ValueError("Could not open the uploaded video")

    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        if not fps or fps <= 0:
            raise ValueError("Could not determine the video's frame rate")

        duration_seconds = frame_count / fps
        frames = []

        timestamp = 0.0

        while timestamp < duration_seconds:
            capture.set(
                cv2.CAP_PROP_POS_MSEC,
                timestamp * 1000,
            )

            success, frame = capture.read()

            if not success:
                timestamp += interval_seconds
                continue

            success, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 85],
            )

            if success:
                image_base64 = base64.b64encode(
                    jpeg.tobytes()
                ).decode("utf-8")

                timestamp_seconds = round(timestamp, 2)
                frames.append(
                    {
                        "filename": _screenshot_filename(
                            len(frames) + 1,
                            timestamp_seconds,
                        ),
                        "timestamp_seconds": timestamp_seconds,
                        "image": f"data:image/jpeg;base64,{image_base64}",
                    }
                )

            timestamp += interval_seconds

        return {
            "duration_seconds": round(duration_seconds, 2),
            "interval_seconds": interval_seconds,
            "total_frames": len(frames),
            "frames": frames,
        }

    finally:
        capture.release()