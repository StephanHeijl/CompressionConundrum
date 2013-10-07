CompressionConundrum
====================
(Comparing one of Windows' Default wallpapers)[http://i44.tinypic.com/2nbdlkj.png]

CompressionConundrum is a Python script that allows you to produce
a large amount of images in different compressions, so that you can find the
most efficient way to send an image to your users. 

This script requires PIL and is optimized for multicore processors. It will
generate images with different qualities and sizes from a source image and output
a large overview of said generations that show the distortion relative to the original
and the decrease (or increase) in size.