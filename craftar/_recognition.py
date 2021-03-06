#  (C) Catchoom Technologies S.L.
#  Licensed under the MIT license.
#  https://github.com/catchoom/craftar-python/blob/master/LICENSE
#  All warranties and liabilities are disclaimed.

""" Provides the function for visual recogn. with CraftAR's API.

Before a single query request is sent, the image is loaded from disk, and,
if needed, transformed (i.e. resized, converted to grayscale, and compressed
as jpeg).
"""

from PIL import Image
from io import BytesIO
from craftar import settings
import requests


def search(token, filename, embed_custom=False, embed_tracking=False,
           bbox=False, app_id=None, strategy="none", version=None, color=False,
           min_size=settings.DEFAULT_QUERY_MIN_SIZE, verbose=False):
    """Performs a visual recognition using CraftAR's API.

    Arguments:
      token          - Token for the target collection.
      filename       - Path to the query image file.
      embed_custom   - custom_data will be embedded.
      embed_tracking - tracking_data will be embedded.
      bbox           - Return bounding boxes.
      app_id         - Application id for signing the tracking data.
      color          - Disables grayscale conversion.
                       Often color images do not give better results.
      min_size       - Sets the shorter dimension for query resizing.
                       The default value provides good recognition
                       results and small round-trip times for most cases.
                       Recognition of objects covering <1/4 of the scene
                       may require higher values.
                       Rescaling can be disabled by using using min_size = -1.
      verbose        - Shows all image transformations performed to the query.
    """
    image = _prepare_image(filename, color, min_size, verbose)

    response = requests.post(
        url="%s/%s/search" % (settings.RECOGNITION_HOSTNAME,
                              settings.RECOGNITION_API_VERSION),
        headers={'User-Agent': settings.USER_AGENT},
        data={
            'token': token,
            'embed_custom': embed_custom and 'true' or 'false',
            'embed_tracking': embed_tracking and 'true' or 'false',
            'bbox': bbox and 'true' or 'false',
            'app_id': app_id,
            'strategy': strategy,
            'version': version,
        },
        files={'image': image},
    )

    return response.json()


def sync(token, app_id, version, bundled=True, tag=None):
    response = requests.post(
        url="%s/%s/sync" % (settings.RECOGNITION_HOSTNAME,
                            settings.RECOGNITION_API_VERSION),
        headers={'User-Agent': settings.USER_AGENT},
        data={
            'token': token,
            'app_id': app_id,
            'version': version,
            'bundled': bundled and 'true' or 'false',
            'tag': tag,
        },
    )

    return response.json()


def _prepare_image(image_file, color=False,
                   min_size=settings.DEFAULT_QUERY_MIN_SIZE, verbose=True):
    """Loads a single query image from disk and prepares it for sending.

    If no conversion is used, then the loaded image is returned unchanged.
    Otherwise, the image is converted using PILLOW and encoded as a JPEG image.
    Arguments:
      image_file - Path to the query image file.
      color      - Disables grayscale conversion.
                   Often color images do not give better result.
      min_size   - Sets the shorter dimension for query resizing.
                   Rescaling can be disabled by using using min_size = -1.
      verbose    - Shows all image transformations performed to the query.
    """
    # check if image conversions needed
    if color and min_size <= 0:
        # no conversion needed so simply open, load, and return the image
        try:
            image = open(image_file, 'rb').read()
        except IOError:
            if verbose:
                print("Image Opening Error!")
            raise
        else:
            if verbose:
                print("Sending Original Image")
            # return the original image
            return image
    else:
        # perform conversions using PIL
        try:
            # open the image using PIL
            image = Image.open(image_file)
        except IOError:
            if verbose:
                print("Image Opening Error!")
            raise

        if not color:
            # convert the image to grayscale
            try:
                image = image.convert("L")
            except IOError:
                if verbose:
                    print("Image Conversion Error!")
                raise
            else:
                if verbose:
                    print("Grayscale Conversion")

        if min_size > 0:
            # resize min of height or width to be 'min_size'px
            xsize, ysize = image.size
            min_img_size = min(xsize, ysize)
            scale_factor = float(min_size) / float(min_img_size)
            newxsize = int(xsize * scale_factor)
            newysize = int(ysize * scale_factor)
            try:
                image = image.resize((newxsize, newysize))
            except IOError:
                if verbose:
                    print("Image Resizing Error")
                raise
            else:
                if verbose:
                    print("Original Image Size (%d,%d)" % (xsize, ysize))
                    print("Sending Query with Size (%d,%d)" % image.size)

        # write the converted image into a buffer performing JPEG encoding
        string_io = BytesIO()
        image.save(string_io, "JPEG", quality=settings.DEFAULT_IMG_QUALITY)

        # return the converted image
        return string_io.getvalue()
