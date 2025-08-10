import glob
import time

import pytest

from steg.frame import Frame
from steg.steg import images_to_video, video_to_images, encode


def test_smoke():
    data_to_encode = b"Hi Mell, I love you!"
    frames = encode(data_to_encode, tile_width=160, tile_height=160, output_path='tests')

    total_bytes_decoded = 0
    for frame_path in frames:
        frame_to_decode = Frame.load_from_file(frame_path)
        decoded = frame_to_decode.decode()
        assert decoded == data_to_encode[total_bytes_decoded:total_bytes_decoded+len(decoded)]
        total_bytes_decoded += len(frame_to_decode)

    assert total_bytes_decoded == len(data_to_encode)

    images_to_video('tests/test_%03d.png', 'tests/test.mp4', framerate=20)
    video_to_images('tests/test.mp4', 'tests/test_videoout%03d.png')

    # I don't have a good way to retrieve these at the moment
    frames = ['tests/test_videoout001.png', 'tests/test_videoout002.png']
    total_bytes_decoded = 0
    for frame_path in frames:
        frame_to_decode = Frame.load_from_file(frame_path)
        decoded = frame_to_decode.decode()
        assert decoded == data_to_encode[total_bytes_decoded:total_bytes_decoded+len(decoded)]
        total_bytes_decoded += len(frame_to_decode)

    assert total_bytes_decoded == len(data_to_encode)


def test_lorem_ipsum():
    with open('tests/test_data/loremipsum.txt', 'rb') as f:
        data_to_encode = f.read()

    frames = encode(data_to_encode, output_path='tests')

    total_bytes_decoded = 0
    for frame_path in frames:
        frame_to_decode = Frame.load_from_file(frame_path)
        decoded = frame_to_decode.decode()
        assert decoded == data_to_encode[total_bytes_decoded:total_bytes_decoded + len(decoded)]
        total_bytes_decoded += len(frame_to_decode)

    assert total_bytes_decoded == len(data_to_encode)

    images_to_video('tests/test_%03d.png', 'tests/test.mp4', framerate=20)
    video_to_images('tests/test.mp4', 'tests/test_videoout%03d.png')

    # I don't have a good way to retrieve these at the moment
    frames = glob.glob('tests/test_videoout*.png')
    total_bytes_decoded = 0
    for frame_path in frames:
        frame_to_decode = Frame.load_from_file(frame_path)
        decoded = frame_to_decode.decode()
        assert decoded == data_to_encode[total_bytes_decoded:total_bytes_decoded + len(decoded)]
        total_bytes_decoded += len(frame_to_decode)

    assert total_bytes_decoded == len(data_to_encode)


@pytest.mark.skip
def test_4mb():
    start = time.time()
    print(f"{start=}")

    # encode
    with open('tests/orig_4MB.jpg', 'rb') as f:
        data = f.read()
    encode(data, tile_width=48, tile_height=48)

    # convert to video
    images_to_video('tests/test_%03d.png', 'tests/test.mp4', framerate=20)

    encode_finished_time = time.time()
    print(f"{encode_finished_time=} -- elapsed: {encode_finished_time - start}s")

    # decode
    video_to_images('test.mp4', 'test_videoout%03d.png')

    with open('test_decode.jpg', 'wb') as f:
        for ii in range(1, 10583):
            frame_to_decode = Frame.load_from_file(f'test_videoout{ii:03d}.png')
            f.write(frame_to_decode.decode())
    decode_finished_time = time.time()
    print(f"{decode_finished_time=} -- elapsed: {decode_finished_time - encode_finished_time}s")


@pytest.mark.skip
def test_youtube():
    video_to_images('test202504072.mkv', 'test_videoout%03d.png')

    with open('test_decode.jpg', 'wb') as f:
        for ii in range(1, 10583):
            print(f"file {ii}:")
            frame_to_decode = Frame.load_from_file(f'test_videoout{ii:03d}.png')
            f.write(frame_to_decode.decode(ignore_errors=True))
