import {createTextureFromSource} from './deps/webgpu-utils-1.11.0-module.js';
import getVideoFrames from "./deps/getVideoFrames.0.0.10.js";

export async function getTextFile(url) {
    return (await fetch(url)).text()
}

const frameDecoderShaderWgsl = await getTextFile('frame_decoder_shader.wgsl');

export async function getImage(url) {
    const file = await fetch(url);
    return await createImageBitmap(await file.blob(), {colorSpaceConversion: 'none'});
}

// untested, i don't use chrome
export async function saveDataToFileChrome(data) {
    const newHandle = await window.showSaveFilePicker();
    const writableStream = await newHandle.createWritable();
    await writableStream.write(data);
    await writableStream.close();
}

// come on firefox
export function saveDataToFileFirefox(data) {
    const blob = new Blob([data], {type: 'application/octet-stream'});
    const blobUrl = URL.createObjectURL(blob);

    const a = document.createElement('a')
    a.href = blobUrl
    a.download = "out.bin"
    document.body.appendChild(a)
    a.style.display = 'none'
    a.click()
    a.remove()
}

export async function decodeFrame(frame) {
    const adapter = await navigator.gpu?.requestAdapter();
    const device = await adapter?.requestDevice();

    const frameDecoderModule = device.createShaderModule({
        label: 'frame decoder shader',
        code: frameDecoderShaderWgsl
    });

    const texture = createTextureFromSource(device, frame);

    const tileWidth = 48;
    const tileHeight = 48;
    const columns = Math.floor(texture.width / tileWidth);
    const rows = Math.floor(texture.height / tileHeight);
    const numTiles = columns * rows;
    const bufferSize = numTiles * 4; // uint32

    const frameDecoderPipeline = device.createComputePipeline({
        label: 'frame decoder' + Math.random().toString(),
        layout: 'auto',
        compute: {
            module: frameDecoderModule,
        },
    });

    // storage buffer for the decoded frame
    const tilesBuffer = device.createBuffer({
        size: bufferSize,
        usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
    });

    // copy destination buffer we'll read back from javascript
    const resultBuffer = device.createBuffer({
        size: bufferSize,
        usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
    });

    const encoder = device.createCommandEncoder({ label: 'frame decoder shader encoder' + Math.random().toString()});
    const pass = encoder.beginComputePass();
    pass.setPipeline(frameDecoderPipeline);
    pass.setBindGroup(0, device.createBindGroup({
        layout: frameDecoderPipeline.getBindGroupLayout(0),
        entries: [
            { binding: 0, resource: { buffer: tilesBuffer }},
            { binding: 1, resource: texture.createView() },
        ],
    }));
    // TODO: possible optimizations: dispatch multi-dimensional workgroups
    pass.dispatchWorkgroups(numTiles);
    pass.end();

    encoder.copyBufferToBuffer(tilesBuffer, resultBuffer);

    const commandBuffer = encoder.finish();
    device.queue.submit([commandBuffer]);

    await resultBuffer.mapAsync(GPUMapMode.READ);
    const resultsUint32 = resultBuffer.getMappedRange().slice(0);
    resultBuffer.unmap();

    // convert uint32's from webgpu to uint8's, essentially stripping away the upper 24 bits of the old uint32's
    // TODO: catch sentinel error value 999
    let results = new Uint8Array(resultsUint32);
    results = results.filter((_, ii) => ii % 4 === 0)

    return results;
}

export async function decodeVideo(video) {
    const promises = [];
    let results = [];
    let frameCount = 0;
    let totalFrames = 0;

    await getVideoFrames({
        videoUrl: video,
        onFrame(frame) {
            let frameNum = frameCount;
            frameCount++;

            const canvas = document.createElement("canvas");
            canvas.width = frame.codedWidth;
            canvas.height = frame.codedHeight;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(frame, 0, 0, canvas.width, canvas.height);

            frame.close();

            promises.push(
                decodeFrame(canvas).then((result) => {
                    results.push([frameNum, result]);
                })
            );
        },
        onConfig(config) {
            totalFrames = config.info.videoTracks[0].nb_samples;
        },
        onFinish() {
            // shrug
        },
    });

    await Promise.all(promises);

    results.sort((a, b) => a[0]-b[0]);
    results = results.map((result) => result[1]);

    let result = new ArrayBuffer(0);
    let view;
    let prevFrameSeqNo = -1;
    let nextFrameSeqNoExpected = 0;
    // reduce the array of uint8arrays down to a single one.
    // a uint8array is backed by an ArrayBuffer of a fixed size, so we need to transfer each one into a new one
    results.forEach((frame, ii, results) => {
        const frameSeqNo = frame[5];
        if (prevFrameSeqNo === frameSeqNo) {
            // duplicate frame, skip
            return;
        }

        if (frameSeqNo !== nextFrameSeqNoExpected) {
            console.log(frameSeqNo, "received out of order, expected", nextFrameSeqNoExpected);
            return;
        }

        prevFrameSeqNo = frameSeqNo;
        nextFrameSeqNoExpected = (frameSeqNo + 1) % 256;

        // header bytes 8 and 9 contain the payload length (16 bits big-endian)
        const len = (frame[8] << 8) + frame[9];
        // note which index we want to insert this frame's payload at
        const bufferFrameStartIndex = result.maxByteLength;
        result = result.transfer(result.maxByteLength + len);
        view = new Uint8Array(result);
        view.set(frame.slice(13, 13 + len), bufferFrameStartIndex);
    })

    return view;
}
