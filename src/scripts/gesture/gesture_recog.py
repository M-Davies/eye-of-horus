# -----------------------------------------------------------
# Runs gesture recognition on the capture frame
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

import boto3
import sys
import os
import argparse

from PIL import Image

sys.path.append(os.path.dirname(__file__) + "/..")
import commons

def checkForGestures(frame, username):
    pass

def main(argv):
    """main() : Main method that parses the input opts and returns the result"""
    # Parse input parameters
    argumentParser = argparse.ArgumentParser(
        description="Runs gesture recognition of an image or video frame against a specific user's gestures",
        formatter_class=argparse.RawTextHelpFormatter
    )
    argumentParser.add_argument("-f", "--file",
        required=True,
        help="Full path to a jpg or png image file (s3 or local)"
    )
    argumentParser.add_argument("-u", "--username",
        required=True,
        help="Username to retrieve the gestures from AWS for comparison with the gestures performed in the image"
    )
    argDict = argumentParser.parse_args()

    # Check if we're using a local file
    if os.path.isfile(argDict.file):
        try:
            Image.open(argDict.file)
        except IOError:
            commons.respond(
                messageType="ERROR",
                message=f"File {argDict.file} exists but is not an image. Only jpg and png files are valid",
                code=7
            )
        checkForGestures(argDict.file, argDict.username)
    else:
        # Use an S3 object if no file was found at the image path given
        print(f"[WARNING] {argDict.file} does not exist as a local file. Attempting to retrieve the image using the same path from S3...")

        # TODO: Either download the image or pass the link to custom labels

if __name__ == "__main__":
    main(sys.argv[1:])