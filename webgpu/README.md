This directory contains a proof of concept WebGPU compute shader implementation of this experiment.

[index.html](index.html) contains a file input element that can be used to select an H.264 MP4 file.

This runs roughly 4-5x faster in Chrome compared to Firefox on my M3 Macbook Air.

## Acknowledgments

The libraries below and their full licenses can be found in the [deps](deps) directory.

`webgpu-utils` is MIT-licensed and comes from https://www.npmjs.com/package/webgpu-utils

`getVideoFrames.js` is MIT-licensed and comes from https://github.com/josephrocca/getVideoFrames.js

`mp4box.js` is BSD-3-licensed and comes from https://github.com/gpac/mp4box.js
