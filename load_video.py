#!/usr/bin/env python3

"""CLI to load data from a video and corresponding OpenPifPaf output into the db."""

import argparse
import asyncio
import logging
from pathlib import Path

import cv2
import numpy as np
from rich.logging import RichHandler

from pose_data_db import PoseDataDatabase
from pose_normalization import (
    extract_trustworthy_coords,
    shift_normalize_rescale_pose_coords,
)


def get_video_metadata(video_file):
    cap = cv2.VideoCapture(str(video_file))
    return {
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "fps": float(cap.get(cv2.CAP_PROP_FPS)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    }


def normalize_pose_data(pose):
    normalized_coords = extract_trustworthy_coords(
        shift_normalize_rescale_pose_coords(pose)
    )
    return normalized_coords


async def main() -> None:
    """Command-line entry-point."""

    parser = argparse.ArgumentParser(description="Description: {}".format(__doc__))
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )

    parser.add_argument(
        "--drop",
        action="store_true",
        default=False,
        help="Drop (if existing) and recreate tables",
    )

    parser.add_argument("--video-path", action="store", required=True)
    parser.add_argument("--json-path", action="store")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=True)],
    )

    video_path = Path(args.video_path)
    assert video_path.exists(), f"'{video_path}' does not exist"

    if args.json_path:
        json_path = Path(args.json_path)
    else:
        json_path = Path(f"{video_path}.openpifpaf.json")
        logging.debug(f"--json-path not supplied, using '{json_path}'")

    assert json_path.exists(), f"'{json_path}' does not exist"

    video_metadata = get_video_metadata(video_path)

    db = await PoseDataDatabase.create(drop=args.drop)
    video_id = await db.add_video(video_path.name, video_metadata)
    await db.load_openpifpaf_predictions(video_id, json_path)
    logging.info("Normalizing pose data, and annotating db records...")
    await db.annotate_pose(
        "norm",
        "vector(34)",
        video_id,
        lambda pose: tuple(np.nan_to_num(normalize_pose_data(pose), nan=-1).tolist()),
    )


if __name__ == "__main__":
    asyncio.run(main())
