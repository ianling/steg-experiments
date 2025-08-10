from steg.steg import encode, images_to_video

def main():
    print("blah")
    with open('tests/test_data/loremipsum.txt', 'rb') as f:
        encode(f.read(), output_path="scripts")
    images_to_video('scripts/test_%03d.png', 'lorem_ipsum.mp4', framerate=1)
