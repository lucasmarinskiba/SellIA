"""compress_image / get_image_dimensions decode bytes downloaded from third-party generation providers.

Only the formats the providers return are accepted; Pillow's decoders for the rest (FPX, TIFF, ...) are where
most of its image-parsing advisories live, so a file in one of those is refused instead of parsed.
"""

import io

import pytest
from PIL import Image, UnidentifiedImageError

from app.integrations.content_generation import utils


def _image_bytes(fmt: str, mode: str = "RGB", size=(64, 48)) -> bytes:
    out = io.BytesIO()
    Image.new(mode, size, (200, 30, 30) if mode == "RGB" else (200, 30, 30, 128)).save(out, format=fmt)
    return out.getvalue()


@pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP", "GIF"])
def test_accepted_formats_compress_and_report_their_size(fmt):
    data = _image_bytes(fmt)
    assert utils.get_image_dimensions(data) == (64, 48)
    compressed = utils.compress_image(data, target_format="JPEG", quality=70)
    assert Image.open(io.BytesIO(compressed)).format == "JPEG"


def test_png_with_alpha_is_flattened_for_jpeg():
    compressed = utils.compress_image(_image_bytes("PNG", mode="RGBA"), target_format="JPEG")
    assert Image.open(io.BytesIO(compressed)).mode == "RGB"


def test_large_images_are_resized_with_the_current_resampling_filter():
    big = _image_bytes("PNG", size=(3000, 1500))
    out = Image.open(io.BytesIO(utils.compress_image(big, max_dimension=1000)))
    assert max(out.size) == 1000


@pytest.mark.parametrize("fmt", ["TIFF", "BMP", "ICO"])
def test_other_formats_are_refused(fmt):
    data = _image_bytes(fmt)
    with pytest.raises(UnidentifiedImageError):
        utils.compress_image(data)
    with pytest.raises(UnidentifiedImageError):
        utils.get_image_dimensions(data)
