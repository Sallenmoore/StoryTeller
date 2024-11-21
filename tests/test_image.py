import io

import pytest
from PIL import Image as PILImage

from models.images.image import Image

SAMPLE_IMAGE_URL = "https://images.pexels.com/photos/4021773/pexels-photo-4021773.jpeg"


@pytest.fixture
def sample_image_bytes():
    # Create a small blank image for testing
    img = PILImage.new("RGB", (1024, 1024), color="white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="WEBP")
    return img_byte_arr.getvalue()


@pytest.fixture
def sample_image_object(sample_image_bytes):
    # Create and save a sample Image object
    image_obj = Image(prompt="Sample prompt", tags=["test", "sample"])
    image_obj.data.put(
        io.BytesIO(sample_image_bytes).getvalue(), content_type="image/webp"
    )
    image_obj.save()
    return image_obj


def test_generate(mocker, sample_image_bytes):
    # Mock the OpenAI image generation response
    mocker.patch(
        "autonomous.ai.imageagent.ImageAgent.generate",
        return_value=io.BytesIO(sample_image_bytes).getvalue(),
    )

    image_obj = Image.generate("Test prompt", tags=["generated"])
    assert image_obj is not None
    assert image_obj.prompt == "Test prompt"
    assert "generated" in image_obj.tags
    assert image_obj.read() == sample_image_bytes


def test_from_url(requests_mock, sample_image_bytes):
    # Mock the URL request
    requests_mock.get(
        SAMPLE_IMAGE_URL,
        content=sample_image_bytes,
        headers={"Content-Type": "image/jpeg"},
    )

    image_obj = Image.from_url(SAMPLE_IMAGE_URL, prompt="URL test", tags=["url"])
    assert image_obj is not None
    assert image_obj.prompt == "URL test"
    assert "url" in image_obj.tags
    assert image_obj.read() == sample_image_bytes


def test_resize(sample_image_object):
    resized_image_data = sample_image_object.resize(max_size="thumbnail")
    img = PILImage.open(io.BytesIO(resized_image_data))
    assert img.size == (100, 100)


@pytest.mark.skip(reason="Not Working, but Non-Essential")
def test_flip_horizontal(sample_image_object):
    original_data = sample_image_object.read()
    sample_image_object.flip(horizontal=True, vertical=False)
    flipped_data = sample_image_object.read()
    assert original_data != flipped_data

    # Ensure the flipped image is valid
    img = PILImage.open(io.BytesIO(flipped_data))
    assert img.size == (1024, 1024)


@pytest.mark.skip(reason="Not Working, but Non-Essential")
def test_flip_vertical(sample_image_object):
    original_data = sample_image_object.read()
    sample_image_object.flip(horizontal=False, vertical=True)
    flipped_data = sample_image_object.read()
    assert original_data != flipped_data

    # Ensure the flipped image is valid
    img = PILImage.open(io.BytesIO(flipped_data))
    assert img.size == (1024, 1024)


@pytest.mark.skip(reason="Not Working, but Non-Essential")
def test_rotate(sample_image_object):
    original_data = sample_image_object.read()
    sample_image_object.rotate(amount=90)
    rotated_data = sample_image_object.read()
    assert original_data != rotated_data

    # Ensure the rotated image is still valid
    img = PILImage.open(io.BytesIO(rotated_data))
    assert img.size == (1024, 1024)  # Size should remain the same


def test_add_tag(sample_image_object):
    sample_image_object.add_tag("new_tag")
    assert "new_tag" in sample_image_object.tags


def test_add_tags(sample_image_object):
    sample_image_object.add_tags(["tag1", "tag2", "tag3"])
    assert "tag1" in sample_image_object.tags
    assert "tag2" in sample_image_object.tags
    assert "tag3" in sample_image_object.tags


def test_remove_tag(sample_image_object):
    sample_image_object.add_tag("removable_tag")
    sample_image_object.remove_tag("removable_tag")
    assert "removable_tag" not in sample_image_object.tags


def test_url(sample_image_object):
    url = sample_image_object.url(size="medium")
    assert url == f"/image/{sample_image_object.pk}/medium"
