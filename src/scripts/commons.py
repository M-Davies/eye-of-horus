# -----------------------------------------------------------
# Storage file for global variables and configs used across all scripts
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# -----------------------------------------------------------

import os
import sys
import json
from dotenv import load_dotenv
load_dotenv()


def respond(messageType, code, message, content=None):
    """respond() : Print/return informational JSON message and sometimes terminate execution
    :param messageType: Type of message (ERROR, SUCCESS, etc)
    :param code: Exit code to terminate execution with
    :param message: Short message to be sent describing the event
    :param content: Optional excess message content (e.g. JSON data) used by the website or other scripts
    """
    jsonMessage = json.dumps(
        obj={
            "TYPE": messageType,
            "MESSAGE": message,
            "CONTENT": json.dumps(content),
            "CODE": code
        },
        indent=2
    )
    print(jsonMessage)

    # Replace response file and exit
    with open(os.getenv("RESPONSE_FILE_PATH"), "w") as logfile:
        logfile.write(jsonMessage)
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
