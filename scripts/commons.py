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

import sys

# GLOBAL VARIABLES USED BY ALL SCRIPTS
FACE_RECOG_BUCKET = "eye-of-horus-bucket"
FACE_RECOG_COLLECTION = "RekognitionCollection"

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
    return objectName

