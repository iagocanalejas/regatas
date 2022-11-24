import logging
from abc import ABC, abstractmethod

import cv2
import numpy as np
from pandas import DataFrame
from pytesseract import pytesseract

from scrappers._scrapper import Scrapper

logger = logging.getLogger(__name__)

IMAGE_INFOREMO = 'inforemo'
IMAGE_KONTXAKO = 'kontxako'


class ImageScrapper(ABC, Scrapper):
    _registry = {}

    def __init_subclass__(cls, **kwargs):
        source = kwargs.pop('source')
        super().__init_subclass__(**kwargs)
        cls._registry[source] = cls

    def __new__(cls, source: str, **kwargs):  # pragma: no cover
        subclass = cls._registry[source]
        final_obj = object.__new__(subclass)

        return final_obj

    @abstractmethod
    def clean_dataframe(self, df: DataFrame) -> DataFrame:
        raise NotImplementedError

    def get_summary_soup(self, img: np.ndarray, img_vh: np.ndarray, optimize: bool, **kwargs) -> DataFrame:
        bitnot = self._retrieve_image_image_vh_bitnot(img, img_vh)
        row, count_col = self._retrieve_grid(img_vh)
        final_boxes = self._retrieve_final_boxes(row, count_col)
        outer = self._process_boxes(final_boxes, bitnot, optimize=optimize)

        # Creating a dataframe of the generated OCR list
        arr = np.array(outer)
        return self.clean_dataframe(DataFrame(arr.reshape(len(row), count_col)))

    def get_race_details_soup(self, img_bin: np.ndarray, optimize: bool = False, **kwargs) -> str:
        image = self._optimize_image(img_bin) if optimize else img_bin

        out = pytesseract.image_to_string(image)
        if not len(out):
            out = pytesseract.image_to_string(image, config='--psm 3')
        return out

    ####################################################
    #                 IMAGE PROCESSING                 #
    ####################################################

    @staticmethod
    def _retrieve_image_vh(img):
        thresh, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        img_bin = 255 - img_bin

        # countcol(width) of kernel as 100th of total width
        kernel_len = np.array(img).shape[1] // 100

        # Defining kernels to detect all lines of image
        ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))
        hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))

        # Use vertical kernel to detect and save the vertical lines in a jpg
        image_1 = cv2.erode(img_bin, ver_kernel, iterations=3)
        vertical_lines = cv2.dilate(image_1, ver_kernel, iterations=3)

        # Use horizontal kernel to detect and save the horizontal lines in a jpg
        image_2 = cv2.erode(img_bin, hor_kernel, iterations=3)
        horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations=3)

        # Combine horizontal and vertical lines in a new third image, with both having same weight.
        img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
        img_vh = cv2.erode(~img_vh, kernel, iterations=2)
        thresh, img_vh = cv2.threshold(img_vh, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        return img_vh, img_bin

    @staticmethod
    def _retrieve_image_image_vh_bitnot(img, img_vh):
        bitxor = cv2.bitwise_xor(img, img_vh)
        bitnot = cv2.bitwise_not(bitxor)

        return bitnot

    @staticmethod
    def _retrieve_boxes(img_vh):
        # Detect contours for following box detection
        contours, hierarchy = cv2.findContours(img_vh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Sort all the contours by top to bottom.
        bounding_boxes = [cv2.boundingRect(c) for c in contours]
        contours, bounding_boxes = zip(*sorted(zip(contours, bounding_boxes), key=lambda b: b[1][1], reverse=False))

        boxes = []
        # Get position (x,y), width and height for every contour and show the contour on image
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w < 1000 and h < 500:
                boxes.append([x, y, w, h])

        return boxes, np.mean([bounding_boxes[i][3] for i in range(len(bounding_boxes))])

    def _retrieve_grid(self, img_vh):
        boxes, height_mean = self._retrieve_boxes(img_vh)
        # Creating two lists to define row and column in which cell is located
        row = []
        column = [boxes[0]]

        # Sorting the boxes to their respective row and column
        previous = boxes[0]
        for i in range(1, len(boxes)):
            if boxes[i][1] <= previous[1] + height_mean / 2:
                column.append(boxes[i])
                previous = boxes[i]
                if i == len(boxes) - 1:
                    row.append(column)
            else:
                row.append(column)
                column = []
                previous = boxes[i]
                column.append(boxes[i])

        # calculating maximum number of cells
        count_col = 0
        for i in range(len(row)):
            count_col = len(row[i])
            if count_col > count_col:
                count_col = count_col

        return row, count_col

    @staticmethod
    def _retrieve_final_boxes(row, count_col):
        last = len(row) - 1

        # Retrieving the center of each column
        center = np.array([int(row[last][j][0] + row[last][j][2] / 2) for j in range(len(row[last])) if row[0]])
        center.sort()

        final_boxes = []
        for i in range(len(row)):
            lis = []
            for k in range(count_col):
                lis.append([])
            for j in range(len(row[i])):
                diff = abs(center - (row[i][j][0] + row[i][j][2] / 4))
                idx = list(diff).index(min(diff))
                lis[idx].append(row[i][j])
            final_boxes.append(lis)
        return final_boxes

    def _process_boxes(self, final_boxes, bitnot, optimize: bool):
        # from every single image-based cell/box the strings are extracted via pytesseract and stored in a list
        outer = []
        for i in range(len(final_boxes)):
            for j in range(len(final_boxes[i])):
                inner = ''
                if len(final_boxes[i][j]) == 0:
                    outer.append(' ')
                    continue

                for k in range(len(final_boxes[i][j])):
                    y, x, w, h = final_boxes[i][j][k][0], final_boxes[i][j][k][1], final_boxes[i][j][k][2], final_boxes[i][j][k][3]
                    finalimg = bitnot[x:x + h, y:y + w]
                    border = cv2.copyMakeBorder(finalimg, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=[255, 255])
                    image = self._optimize_image(border) if optimize else border

                    out = pytesseract.image_to_string(image, config='--psm 4')
                    if len(out) == 0:
                        out = pytesseract.image_to_string(image, config='--psm 10')
                    inner = inner + " " + out
                outer.append(inner)
        return outer

    @staticmethod
    def _optimize_image(img: np.ndarray) -> np.ndarray:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
        resizing = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        dilation = cv2.dilate(resizing, kernel, iterations=1)
        erosion = cv2.erode(dilation, kernel, iterations=1)
        return erosion
