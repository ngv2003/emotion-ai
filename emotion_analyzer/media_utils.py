# ---- coding: utf-8 ----
# ===================================================
# Author: Susanta Biswas
# ===================================================
"""Description: Helper methods for media operations."""
# ===================================================
from typing import List, Tuple

import cv2
import dlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from emotion_analyzer.exceptions import InvalidImage
from emotion_analyzer.validators import is_valid_img


# truetype font
warning_font = ImageFont.truetype("data/Ubuntu-R.ttf", 20)
annotation_font = ImageFont.truetype("data/Ubuntu-R.ttf", 16)
bbox_font = ImageFont.truetype("data/Ubuntu-R.ttf", 16)

def convert_to_rgb(image):
    """Converts an image to RGB format.

    Args:
        image (numpy array): [description]

    Raises:
        InvalidImage: [description]

    Returns:
        [type]: [description]
    """
    if not is_valid_img(image):
        raise InvalidImage
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def convert_to_dlib_rectangle(bbox):
    """Converts a bounding box coordinate list
    to dlib rectangle.

    Args:
        bbox (List[int]): Bounding box coordinates

    Returns:
        dlib.rectangle: Dlib rectangle
    """
    return dlib.rectangle(bbox[0], bbox[1], bbox[2], bbox[3])


def load_image_path(img_path, mode: str = "rgb"):
    """Loads image from disk. Optional mode
    to load in RGB mode

    Args:
        img_path (numpy array): [description]
        mode (str, optional): Whether to load in RGB format.
            Defaults to 'rgb'.

    Raises:
        exc: [description]

    Returns:
        [type]: [description]
    """
    try:
        img = cv2.imread(img_path)
        if mode == "rgb":
            return convert_to_rgb(img)
        return img
    except Exception as exc:
        raise exc


def draw_bounding_box(image, bbox: List[int], color: Tuple = (0, 255, 0)):
    """Used for drawing bounding box on an image

    Args:
        image (numpy array): [description]
        bbox (List[int]): Bounding box coordinates
        color (Tuple, optional): [description]. Defaults to (0,255,0).

    Returns:
        [type]: [description]
    """
    x1, y1, x2, y2 = bbox
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    return image


def draw_bounding_box_annotation(image, label: str, bbox: List[int], color: Tuple = (84, 247, 131)):
    """Used for drawing bounding box and label on an image

    Args:
        image (numpy array): [description]
        name (str): Label to annotate
        bbox (List[int]): Bounding box coordinates
        color (Tuple, optional): [description]. Defaults to (0,255,0).

    Returns:
        [type]: [description]
    """
    x1, y1, x2, y2 = bbox
    # Make the bbox a bit taller than usual to cover the face properly
    draw_bounding_box(image, [x1, y1, x2, y2 + 20], color=color)

    # Draw the label with name below the face
    cv2.rectangle(image, (x1, y2), (x2, y2 + 20), color, cv2.FILLED)
    pil_img = Image.fromarray(image)
    
    # PIL drawing context
    draw = ImageDraw.Draw(pil_img)
    draw.text((x1 + 20, y2 + 2), label, (0, 0, 0), font=bbox_font)

    # Convert PIL img to numpy array type
    return np.array(pil_img)


def annotate_warning(warning_text: str, img):
    """Draws warning text at the bottom of screen

    Args:
        warning_text (str): warning label
        img (numpy array): input image
    """
    h, _, _ = img.shape
    x, y = 150, h - 100

    pil_img = Image.fromarray(img.copy())
    
    # PIL drawing context
    draw = ImageDraw.Draw(pil_img)
    draw.text((x+1, y+1), warning_text, (0, 0, 0), font=warning_font)
    draw.text((x, y), warning_text, (12, 52, 242), font=warning_font)

    warning_text = "Emotion chart will be shown for one person only!"
    draw.text((x, y+31), warning_text, (255, 255, 255), font=warning_font)

    # Convert PIL img to numpy array type
    return np.array(pil_img)


def annotate_emotion_stats(emotion_data, img):
    """Draws a bar chart of emotion labels on top of image

    Args:
        emotion_data (Dict): Emotions and their respective prediction confidence
        img (numpy array): input image
    """

    for index, emotion in enumerate(emotion_data.keys()):
        # for drawing progress bar
        cv2.rectangle(img, (100, index * 20 + 20), (100 + int(emotion_data[emotion]), (index + 1) * 20 + 18),
                        (255, 0, 0), -1)

    # convert to PIL format image
    pil_img = Image.fromarray(img.copy())
    # PIL drawing context
    draw = ImageDraw.Draw(pil_img)
    
    for index, emotion in enumerate(emotion_data.keys()):
        # for putting emotion labels
        draw.text((10, index * 20 + 20), emotion, (7, 109, 16), font=annotation_font)
        
        emotion_confidence = str(emotion_data[emotion]) + "%"
        # for putting percentage confidence
        draw.text((105 + int(emotion_data[emotion]), index * 20 + 20), emotion_confidence, (255, 0, 0), font=annotation_font)
        
    # Convert PIL img to numpy array type
    return np.array(pil_img)
        

def draw_emoji(emoji, img):
    """Puts an emoji img on top of another image.

    Args:
        emoji (numpy array): emoji picture
        img (numpy array): input image
    """
    # overlay emoji on the frame for all the channels
    for c in range(0, 3):
        # for doing overlay we need to assign weights to both foreground and background
        foreground = emoji[:, :, c] * (emoji[:, :, 3] / 255.0)
        background = img[350:470, 10:130, c] * (1.0 - emoji[:, :, 3] / 255.0)
        img[350:470, 10:130, c] = foreground + background

    return img


def get_facial_ROI(image, bbox: List[int]):
    """Extracts the facial region in an image
    using the bounding box coordinates.

    Args:
        image ([type]): [description]
        bbox (List[int]): [description]

    Raises:
        InvalidImage: [description]

    Returns:
        [type]: [description]
    """
    if image is None or bbox is None:
        raise InvalidImage if image is None else ValueError
    return image[bbox[1] : bbox[3], bbox[0] : bbox[2], :]


def get_video_writer(video_stream, output_filename: str = "data/output.mp4"):
    """Returns an OpenCV video writer with mp4 codec stream

    Args:
        video_stream (OpenCV video stream obj): Input video stream
        output_filename (str):

    Returns:
        OpenCV VideoWriter:
    """
    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        FPS = video_stream.get(cv2.CAP_PROP_FPS)

        # (Width, Height)
        dims = (int(video_stream.get(3)), int(video_stream.get(4)))
        video_writer = cv2.VideoWriter(output_filename, fourcc, FPS, dims)
        return video_writer
    except Exception as exc:
        raise exc
