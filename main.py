from cscore import CameraServer
from networktables import NetworkTables
import numpy
import cv2
from enum import Enum


class GripPipeline:
    """
    An OpenCV pipeline generated by GRIP.
    """

    def __init__(self, threshold_hue, threshold_saturation, threshold_value):
        """initializes all values to presets or None if need to be set
        """

        self.__resize_image_width = 160.0
        self.__resize_image_height = 90.0
        self.__resize_image_interpolation = cv2.INTER_CUBIC

        self.resize_image_output = None

        self.__hsv_threshold_input = self.resize_image_output
        self.__hsv_threshold_hue = threshold_hue
        self.__hsv_threshold_saturation = threshold_saturation
        self.__hsv_threshold_value = threshold_value

        self.hsv_threshold_output = None

        self.__cv_erode_src = self.hsv_threshold_output
        self.__cv_erode_kernel = None
        self.__cv_erode_anchor = (-1, -1)
        self.__cv_erode_iterations = 0.5
        self.__cv_erode_bordertype = cv2.BORDER_CONSTANT
        self.__cv_erode_bordervalue = (-1)

        self.cv_erode_output = None

        self.__cv_dilate_src = self.cv_erode_output
        self.__cv_dilate_kernel = None
        self.__cv_dilate_anchor = (-1, -1)
        self.__cv_dilate_iterations = 1.0
        self.__cv_dilate_bordertype = cv2.BORDER_CONSTANT
        self.__cv_dilate_bordervalue = (-1)

        self.cv_dilate_output = None

    def process(self, source0):
        """
        Runs the pipeline and sets all outputs to new values.
        """
        # Step Resize_Image0:
        self.__resize_image_input = source0
        (self.resize_image_output) = self.__resize_image(self.__resize_image_input, self.__resize_image_width, self.__resize_image_height, self.__resize_image_interpolation)

        # Step HSV_Threshold0:
        self.__hsv_threshold_input = self.resize_image_output
        (self.hsv_threshold_output) = self.__hsv_threshold(self.__hsv_threshold_input, self.__hsv_threshold_hue, self.__hsv_threshold_saturation, self.__hsv_threshold_value)

        # Step CV_erode0:
        self.__cv_erode_src = self.hsv_threshold_output
        (self.cv_erode_output) = self.__cv_erode(self.__cv_erode_src, self.__cv_erode_kernel, self.__cv_erode_anchor, self.__cv_erode_iterations, self.__cv_erode_bordertype, self.__cv_erode_bordervalue)

        # Step CV_dilate0:
        self.__cv_dilate_src = self.cv_erode_output
        (self.cv_dilate_output) = self.__cv_dilate(self.__cv_dilate_src, self.__cv_dilate_kernel, self.__cv_dilate_anchor, self.__cv_dilate_iterations, self.__cv_dilate_bordertype, self.__cv_dilate_bordervalue)

    @staticmethod
    def __resize_image(input, width, height, interpolation):
        """Scales and image to an exact size.
        Args:
            input: A numpy.ndarray.
            Width: The desired width in pixels.
            Height: The desired height in pixels.
            interpolation: Opencv enum for the type fo interpolation.
        Returns:
            A numpy.ndarray of the new size.
        """
        return cv2.resize(input, ((int)(width), (int)(height)), 0, 0, interpolation)

    @staticmethod
    def __hsv_threshold(input, hue, sat, val):
        """Segment an image based on hue, saturation, and value ranges.
        Args:
            input: A BGR numpy.ndarray.
            hue: A list of two numbers the are the min and max hue.
            sat: A list of two numbers the are the min and max saturation.
            lum: A list of two numbers the are the min and max value.
        Returns:
            A black and white numpy.ndarray.
        """
        out = cv2.cvtColor(input, cv2.COLOR_BGR2HSV)
        return cv2.inRange(out, (hue[0], sat[0], val[0]), (hue[1], sat[1], val[1]))

    @staticmethod
    def __cv_erode(src, kernel, anchor, iterations, border_type, border_value):
        """Expands area of lower value in an image.
        Args:
           src: A numpy.ndarray.
           kernel: The kernel for erosion. A numpy.ndarray.
           iterations: the number of times to erode.
           border_type: Opencv enum that represents a border type.
           border_value: value to be used for a constant border.
        Returns:
            A numpy.ndarray after erosion.
        """
        return cv2.erode(src, kernel, anchor, iterations=(int)(iterations + 0.5),
                         borderType=border_type, borderValue=border_value)

    @staticmethod
    def __cv_dilate(src, kernel, anchor, iterations, border_type, border_value):
        """Expands area of higher value in an image.
        Args:
           src: A numpy.ndarray.
           kernel: The kernel for dilation. A numpy.ndarray.
           iterations: the number of times to dilate.
           border_type: Opencv enum that represents a border type.
           border_value: value to be used for a constant border.
        Returns:
            A numpy.ndarray after dilation.
        """
        return cv2.dilate(src, kernel, anchor, iterations=(int)(iterations + 0.5),
                          borderType=border_type, borderValue=border_value)


def main():
    team_color = "red"

    red_hue_threshold = [0, 19]
    red_saturation_threshold = [101, 178]
    red_value_threshold = [74, 174]

    blue_hue_threshold = [97, 109]
    blue_saturation_threshold = [83, 225]
    blue_value_threshold = [66, 181]

    # red_hue_threshold = [0.0, 22.0]
    # red_saturation_threshold = [76.17461099255837, 254.73577810920378]
    # red_value_threshold = [64.20863309352518, 254.14949555665729]
    #
    # blue_hue_threshold = [96.0, 109.0]
    # blue_saturation_threshold = [76.17461099255837, 254.73577810920378]
    # blue_value_threshold = [64.20863309352518, 254.14949555665729]

    left_threshold = 0.48
    right_threshold = 0.52

    bottom_threshold = 0.9

    screen_width = 160
    screen_height = 90

    # ----------------------------

    cserver = CameraServer()
    cserver.startAutomaticCapture()

    input_stream = cserver.getVideo()
    img = numpy.zeros(shape=(screen_width, screen_height, 3), dtype=numpy.uint8)

    NetworkTables.initialize(server='10.22.64.2')
    vision_nt = NetworkTables.getTable('Vision')

    if team_color == "red":
        pipeline = GripPipeline(red_hue_threshold, red_saturation_threshold, red_value_threshold)
    else:
        pipeline = GripPipeline(blue_hue_threshold, blue_saturation_threshold, blue_value_threshold)

    while True:
        frame_time, input_img = input_stream.grabFrame(img)

        pipeline.process(input_img)
        output_image = numpy.array(pipeline.hsv_threshold_output)

        circles = cv2.HoughCircles(output_image, cv2.HOUGH_GRADIENT, 1, minDist=10, param1=100, param2=10, minRadius=5, maxRadius=160)

        best_detection = None
        biggest_radius = 0

        if circles is not None:
            for circle in circles[0, :]:
                x, y, r = int(circle[0]), int(circle[1]), int(circle[2])

                if r > biggest_radius:
                    biggest_radius = r
                    best_detection = [x, y, r]

        heading = 0
        close_to_bottom = 0

        if best_detection:
            if 0 < best_detection[0] < (screen_width * left_threshold):
                heading = -1
            elif best_detection[0] > (screen_width * right_threshold):
                heading = 1
            else:
                heading = 2

            if best_detection[1] > (screen_height * bottom_threshold):
                close_to_bottom = 1

        vision_nt.putNumber('x', int(best_detection[0]))
        vision_nt.putNumber('y', int(best_detection[1]))
        vision_nt.putNumber('r', int(best_detection[2]))
        vision_nt.putNumber('bottom', close_to_bottom)
        vision_nt.putNumber('heading', heading)


if __name__ == '__main__':
    main()
