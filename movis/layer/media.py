from __future__ import annotations

from pathlib import Path
from typing import Sequence

import imageio
import numpy as np
from PIL import Image as PILImage

from .mixin import TimelineMixin


class Image:
    """Still image layer to encapsulate various formats of image data and offer
    time-based keying.

    Args:
        img_file: the source of the image data. It can be a file path (``str`` or ``Path``),
            a `PIL.Image` object, or a two or three-dimensional ``numpy.ndarray`` with a shape of ``(H, W, C)``.
        duration: the duration for which the image should be displayed.
            Default is ``1000000.0`` (long enough time).
    """
    def __init__(
        self,
        img_file: str | Path | PILImage.Image | np.ndarray,
        duration: float = 1e6
    ) -> None:
        self.image: np.ndarray | None = None
        self._img_file: Path | None = None
        if isinstance(img_file, (str, Path)):
            self._img_file = Path(img_file)
            assert self._img_file.exists(), f"{self._img_file} does not exist"
        elif isinstance(img_file, PILImage.Image):
            image = np.asarray(img_file.convert("RGBA"))
            self.image = image
        elif isinstance(img_file, np.ndarray):
            if img_file.ndim == 2:
                assert img_file.dtype == np.uint8
                img = np.expand_dims(img_file, axis=-1)
                img = np.concatenate([
                    np.repeat(img, 3, axis=-1),
                    np.full_like(img, 255, dtype=np.uint8)],
                    axis=-1)
                self.image = img
            elif img_file.ndim == 3:
                assert img_file.shape[2] == 4, "Image must have 4 channels (RGBA)"
                self.image = img_file
            else:
                raise ValueError(f"Invalid img_file shape: {img_file.shape}")
        else:
            raise ValueError(f"Invalid img_file type: {type(img_file)}")

        self._duration = duration

    @property
    def duration(self) -> float:
        """The duration for which the image should be displayed."""
        return self._duration

    @property
    def size(self) -> tuple[int, int]:
        """The size of the image with a tuple of `(width, height)`."""
        shape = self._read_image().shape[:2]
        return shape[1], shape[0]

    def get_key(self, time: float) -> bool:
        """Get the state index for the given time."""
        return 0 <= time < self.duration

    def _read_image(self) -> np.ndarray:
        if self.image is None:
            assert self._img_file is not None
            image = np.asarray(PILImage.open(self._img_file).convert("RGBA"))
            self.image = image
        return self.image

    def __call__(self, time: float) -> np.ndarray | None:
        return self._read_image()


class ImageSequence(TimelineMixin):
    """Image sequence layer to encapsulate various formats of images.

    Args:
        start_times:
            a sequence of start times for each image.
        end_times:
            a sequence of end times for each image.
        img_files:
            a sequence of image data. Each element can be a file path (``str`` or ``Path``),
            a `PIL.Image` object, or a two or four-dimensional ``numpy.ndarray`` with a shape of ``(H, W, C)``.
    """

    @classmethod
    def from_files(
        cls,
        img_files: Sequence[str | Path | PILImage.Image | np.ndarray],
        each_duration: float = 1.0
    ) -> "ImageSequence":
        """Create an ``ImageSequence`` object from a sequence of image files.

        Different from ``ImageSequence.__init__``, this method does not require the start and end times,
        and the duration for each image is set to ``each_duration``.

        Args:
            img_files:
                a sequence of image data. Each element can be a file path (``str`` or ``Path``),
                a `PIL.Image` object, or a two or four-dimensional ``numpy.ndarray`` with a shape of ``(H, W, C)``.
            each_duration:
                the duration for which each image should be displayed. Default is ``1.0``.

        Returns:
            An ``ImageSequence`` object.
        """
        start_times = np.arange(len(img_files)) * each_duration
        end_times = start_times + each_duration
        return cls(start_times.tolist(), end_times.tolist(), img_files)

    @classmethod
    def from_dir(
        cls,
        img_dir: str | Path,
        each_duration: float = 1.0
    ) -> "ImageSequence":
        """Create an ``ImageSequence`` object from a directory of image files.

        Args:
            img_dir:
                a directory containing image files.
            each_duration:
                the duration for which each image should be displayed. Default is ``1.0``.

        Returns:
            An ``ImageSequence`` object.
        """
        img_dir = Path(img_dir)
        exts = set([".png", ".jpg", ".jpeg", ".bmp", ".tiff"])
        img_files = [
            p for p in sorted(img_dir.glob("*")) if p.is_file() and p.suffix in exts]
        return cls.from_files(img_files, each_duration)

    def __init__(
        self,
        start_times: Sequence[float],
        end_times: Sequence[float],
        img_files: Sequence[str | Path | PILImage.Image | np.ndarray]
    ) -> None:
        super().__init__(start_times, end_times)
        self.img_files = img_files
        self.images: list[np.ndarray | None] = [None] * len(img_files)
        for i, img_file in enumerate(img_files):
            if isinstance(img_file, (str, Path)):
                img_file = Path(img_file)
                assert Path(img_file).exists(), f"{img_file} does not exist"
            elif isinstance(img_file, PILImage.Image):
                self.images[i] = np.asarray(img_file.convert("RGBA"))
            elif isinstance(img_file, np.ndarray):
                self.images[i] = img_file
            else:
                raise ValueError(f"Invalid img_file type: {type(img_file)}")

    def get_key(self, time: float) -> int:
        """Get the state index for the given time."""
        idx = self.get_state(time)
        if idx < 0:
            return -1
        return idx

    def __call__(self, time: float) -> np.ndarray | None:
        idx = self.get_state(time)
        if idx < 0:
            return None
        if self.images[idx] is None:
            img_file = self.img_files[idx]
            assert isinstance(img_file, (str, Path))
            image = np.asarray(PILImage.open(img_file).convert("RGBA"))
            self.images[idx] = image
        return self.images[idx]


class Video:
    """Video layer to encapsulate various formats of video data.

    Args:
        video_file: the source of the video data. It can be a file path (``str`` or ``Path``).
    """

    def __init__(self, video_file: str | Path) -> None:
        self.video_file = Path(video_file)
        self._reader = imageio.get_reader(video_file)
        meta_data = self._reader.get_meta_data()
        self._fps = meta_data["fps"]
        self._size = meta_data["size"]
        self._n_frame = meta_data["nframes"]
        self._duration = meta_data["duration"]

    @property
    def fps(self) -> float:
        """The frame rate of the video."""
        return self._fps

    @property
    def size(self) -> tuple[int, int]:
        """The size of the video with a tuple of ``(width, height)``."""
        return self._size

    @property
    def n_frame(self) -> int:
        """The number of frames in the video."""
        return self._n_frame

    @property
    def duration(self) -> float:
        """The duration of the video."""
        return self._duration

    def get_key(self, time: float) -> int:
        """Get the state index for the given time."""
        if time < 0 or self.duration < time:
            return -1
        frame_index = int(time * self._fps)
        return frame_index

    def __call__(self, time: float) -> np.ndarray | None:
        frame_index = int(time * self._fps)
        frame = self._reader.get_data(frame_index)
        pil_frame = PILImage.fromarray(frame).convert("RGBA")
        return np.asarray(pil_frame)
