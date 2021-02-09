# -----------------------------------------------------------
# Storage file for global variables and configs used across all scripts
#
# Copyright (c) 2020 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

#############################################
# ERROR CODE REFERENCE
# --------------------
# 1 - General
# 2 - Command or param issue
# 3 - Something wasn't found or is invalid
#############################################

from dotenv import load_dotenv
import sys
import os

# GLOBAL VARIABLES USED BY ALL SCRIPTS
FACE_RECOG_BUCKET = "eye-of-horus-bucket"
FACE_RECOG_COLLECTION = "RekognitionCollection"
FACE_RECOG_PROCESSOR = "CameraStreamProcessor"
CAMERA_DATASTREAM_NAME = "AmazonRekognitionCameraDataStream"
CAMERA_STREAM_NAME = "CameraVideoStream"

THROWABLE_ERRORS = ["ERROR", "EXCEPTION"]

def throw(errorType, message, code=None):
    """throw() : Print infomational message and terminate execution
    :param errorType: Type of error message (ERROR, WARNING, etc)
    :param message: Message to be sent alongside the errorType
    :param code: Exit code to terminate execution with
    """

    print(f"[{errorType}] {message}")
    if errorType in THROWABLE_ERRORS:
        sys.exit(code)

def parseObjectName(fileName):
    """parseObjectName() : Produces a single word identifier for an image
    :param fileName: Full path to an S3 or local file
    :return: The identifier to be assigned
    """

    objectName = fileName
    if "/" in fileName:
        objectName = fileName.split("/")[-1]

    objectName = parseImageObject(objectName)

    return objectName

def parseImageObject(objectName):
    """parseImageObject() : Ensures that an object name is an image and appends jpg if it isn't
    :param objectName: Objectname to be checked and modified
    :return: The new objectName
    """

    if "jpg" not in objectName and "png" not in objectName:
        return f"{objectName}.jpg"
    else:
        return objectName

