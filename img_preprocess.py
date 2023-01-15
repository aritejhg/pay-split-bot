"""
denoise -> gray -> remove_shadow -> threshold -> rotate

just call img_preprocess(img) to get the processed image
"""

import cv2
import numpy as np
import os
import pytesseract
import imutils

def preprocess_img(img_path):
    # img = cv2.imread(img_path)
    denoised = denoise(img_path)
    gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
    gray = remove_shadow(gray)
    thresh = threshold(gray)
    rotated = rotate(thresh)
    return rotated

def threshold(img):
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

def rotate(img):
    results = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
    rotated = imutils.rotate_bound(img, angle=-results["rotate"])
    return rotated

def denoise(img):
    return cv2.fastNlMeansDenoisingColored(img,None,7,20,7,21)


def remove_shadow(img):
    rgb_planes = cv2.split(img)

    result_planes = []
    result_norm_planes = []
        
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(diff_img,None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        # result_planes.append(diff_img)
        result_norm_planes.append(norm_img)
        
    # result = cv2.merge(result_planes)
    result_norm = cv2.merge(result_norm_planes)
    return result_norm
