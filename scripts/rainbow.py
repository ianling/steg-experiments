from steg.steg import encode, images_to_video

def main():
    data = b''.join([x.to_bytes() for x in range(256)])
    encode(data, output_path="scripts")
    images_to_video('scripts/test_%03d.png', 'rainbow.mp4', framerate=1)
