# Device showcase video

Vertical (1080x1920, 30fps) store showcase edit, no text, no audio.

1. Make 1080x1920 SDR proxies of the source clips. The iPhone HLG clips need tone-mapping:
   `scale=1080:1920,zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`
2. `python3 edit.py <proxy_dir> <work_dir> <out.mp4>` (add `--fresh` to re-render cached segments).

The edit has two parts. First the devices on display, with speed changes, push-in zoom and varied
transitions. Then the devices in hand, with hard-cut swaps and motion-blurred whips through the store.
A colour grade, light leaks and film grain run across the whole video.
