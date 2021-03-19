# -----------------------------------------------------------
# Runs gesture recognition on the capture frame to see if it contains a gesture. Will check if a user posses such a gesture in their pattern if so.
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# -----------------------------------------------------------

import boto3
from botocore.exceptions import WaiterError, ClientError, HTTPClientError
from ratelimit import limits

rekogClient = boto3.client('rekognition')
s3Client = boto3.client('s3')

import sys
import os
import argparse
import time
import json
import numpy
from pathlib import Path

from PIL import Image

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(__file__) + "/..")
import commons

def getUserCombinationFile(username):
    """getUserCombinationFile() : Retrieves a user's gesture configuration file contents
    :param username: The user to retrieve the config file for
    """
    try:
        return json.loads(s3Client.get_object(
            Bucket=commons.FACE_RECOG_BUCKET,
            Key=f"users/{username}/gestures/GestureConfig.json"
        )["Body"].read())
    except s3Client.exceptions.NoSuchKey:
        return commons.respond(
            messageType="ERROR",
            message=f"No such user gesture config file exists in S3. Does this user exist?",
            code=9
        )
    except Exception as e:
        return commons.respond(
            messageType="ERROR",
            message="Failed to retrieve user gesture config file. Please check your internet connection.",
            content={ "ERROR" : str(e) },
            code=2
        )

@limits(calls=100, period=300)
def inUserCombination(gestureJson, username, locktype, position, userCombination=None):
    """inUserCombination() : Calculates if the given gesture is in the user's combination and in the correct position. This is ratelimited to try and avoid bruteforcing.
    :param gestureJson: Identified gesture JSON object returned from AWS detect_custom_labels
    :param username: User to pull gesture combination
    :param locktype: Whether we are locking or unlocking
    :param position: Position in the combination we are checking for the gestureJson
    :param userCombination: Optional user combination dictionary to compare against
    :return: Boolean denoting if the given gesture and position are both valid in the user's gesture combination
    """
    # Retrieve user's gesture config file
    if userCombination is None:
        gestureConfig = getUserCombinationFile(username)
    else:
        gestureConfig = userCombination

    # Is the stored gesture type and position a match for the detected gesture type and position?
    if gestureConfig[locktype][position]["gesture"] == gestureJson["Name"]:
        return True
    else:
        return False

def getGestureTypes():
    """getGestureTypes() : Gets a list of viable gesture types based off the rekognition project labels. Unfortunately, rekognition does not support pulling labels from a project directly so we will have to settle with pulling them from s3 instead
    :return: List of viable gestures
    """
    # This essentially retrieves all possible gestures, splits path by delimiter and removes the excess empty strings
    prefixPathSplits = list(map(lambda jsonObject: list(filter(None, jsonObject["Prefix"].split("/"))),
        s3Client.list_objects_v2(
            Bucket=commons.FACE_RECOG_BUCKET,
            Prefix="gestureTraining/",
            Delimiter="/"
        )["CommonPrefixes"]
    ))
    # Finally, we return only the middle folder (the label name) and discard the root folder name
    return list(map(lambda prefixPathSplit: prefixPathSplit[-1], prefixPathSplits))

def checkForGestures(image):
    """checkForGestures() : Queries the latest AWS Custom Label model for the gesture metadata. I.e. Does this image contain a gesture and if so, which one is it most likely?
    :param image: Locally stored image OR image bytes OR stream frame to scan for authentication gestures
    :return: JSON object containing the gesture with the highest confidence OR None if no recognised gesture was found
    """
    confidence = 85
    arn = os.getenv("LATEST_MODEL_ARN")

    # The param given are file bytes from an streamed image
    try:
        detectedLabels = rekogClient.detect_custom_labels(
            Image={
                'Bytes': image,
            },
            MinConfidence=confidence,
            ProjectVersionArn=arn
        )['CustomLabels']
    except HTTPClientError:
        # Special case as when the signal handler cancels the script during a detect labels, it will raise this exception
        raise TimeoutError
    except rekogClient.exceptions.InvalidImageFormatException:
        # The param given is hopefully a local image file
        print(f"[INFO] Analysing image to see if it contains a recognised gesture...")
        if os.path.isfile(image):
            with open(image, "rb") as fileBytes:
                # This may throw a ImageTooLargeException as the max allowed by AWS in byte format is 4mb (we let the caller deal with that)
                try:
                    detectedLabels = rekogClient.detect_custom_labels(
                        Image={
                            'Bytes': fileBytes.read(),
                        },
                        MinConfidence=confidence,
                        ProjectVersionArn=arn
                    )['CustomLabels']
                except ClientError as e:
                    # On rare occassions, image is too big for AWS and will fail to process client side rather than server side
                    return commons.respond(
                        messageType="ERROR",
                        message=f"An error occured while processing {image} prior to uploading. Image may be too large for AWS to handle, try cropping or compressing the problamatic image.",
                        content={ "ERROR" : str(e) },
                        code=25
                    )
        else:
            # The param given is a file path to an image in s3
            print("[WARNING] Given parameter is not image bytes or a local image, likelihood is we are dealing with an s3 object path...")
            try:
                detectedLabels = rekogClient.detect_custom_labels(
                    Image={
                        'S3Object': {
                            'Bucket' : commons.FACE_RECOG_BUCKET,
                            'Name' : image,
                        }
                    },
                    MinConfidence=confidence,
                    ProjectVersionArn=arn
                )['CustomLabels']
            except Exception as e:
                # The param given is none of the above
                return commons.respond(
                    messageType="ERROR",
                    message=f"{image} is an invalid object to analyse for custom labels or another exception occurred",
                    content={ "ERROR" : str(e) },
                    code=7
                )

    # Extract gesture with highest confidence (or None if no gesture found)
    try:
        foundGesture = max(detectedLabels, key = lambda ev: ev["Confidence"])
        if foundGesture is not None:
            # FIXME: Remove this
            print(f"[INFO] Found a gesture!\n{foundGesture}")
            return foundGesture
        else:
            # Leave no gesture handling to caller (same applies to a value error which equates to the same thing)
            return None
    except ValueError:
        return None

def getProjectVersions():
    """getProjectVersions() : Retrieves all versions of the custom labels model. Often, we will only use the first/latest version as that is generally the most accurate and up-to-date
    :return: List of project version in chronological order (latest to oldest)
    """
    try:
        return rekogClient.describe_project_versions(
            ProjectArn=os.getenv("PROJECT_ARN"),
            VersionNames=[
                os.getenv("LATEST_MODEL_VERSION"),
            ]
        )["ProjectVersionDescriptions"]
    except Exception as e:
        return commons.respond(
            messageType="ERROR",
            message="Failed to retrieve project version descriptions. Please check your internet connection and .env file.",
            content={ "ERROR" : str(e) },
            code=2
        )

def projectHandler(start):
    """projectHandler() : Starts or stops the custom labels project in AWS. It will wait for the project to boot up after starting and will verify the project actually stopped after stopping.
    :param start: Boolean denoting whether we are starting or stopping the project
    :return: Error code and execution exit if request failed. True otherwwise.
    """
    # Only bother retrieving the newest version
    versionDetails = getProjectVersions()[0]

    if start:
        # Verify that the latest rekognition model is running
        print(f"[INFO] Checking if {commons.GESTURE_RECOG_PROJECT_NAME} has already been started...")

        if versionDetails["Status"] == "STOPPED" or versionDetails["Status"] == "TRAINING_COMPLETED":
            print(f"[INFO] {commons.GESTURE_RECOG_PROJECT_NAME} is not running. Starting latest model for this project (created at {versionDetails['CreationTimestamp']}) now...")

            # Start it and wait to be in a usable state
            try:
                rekogClient.start_project_version(
                    ProjectVersionArn=os.getenv("LATEST_MODEL_ARN"),
                    MinInferenceUnits=1 # Stick to one unit to save money
                )
            except rekogClient.exceptions.ResourceInUseException as e:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Failed to start {commons.GESTURE_RECOG_PROJECT_NAME}. System is in use (e.g. starting or stopping).",
                    code=14
                )
            except Exception as e:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Failed to start {commons.GESTURE_RECOG_PROJECT_NAME}.",
                    content={ "ERROR" : str(e) },
                    code=14
                )

            delay = 25
            maxAttempts = 38
            timeoutSeconds = delay * maxAttempts

            print(f"[INFO] {commons.GESTURE_RECOG_PROJECT_NAME} has been started. Waiting {timeoutSeconds}s for confirmation from AWS...")
            waitHandler = rekogClient.get_waiter('project_version_running')
            try:
                waitHandler.wait(
                    ProjectArn=os.getenv("PROJECT_ARN"),
                    WaiterConfig={
                        "Delay" : delay,
                        "MaxAttempts" : maxAttempts
                    }
                )
            except WaiterError:
                return commons.respond(
                    messageType="ERROR",
                    message=f"{commons.GESTURE_RECOG_PROJECT_NAME} FAILED to start properly before {timeoutSeconds}s timeout expired. Model is likely still booting up",
                    code=15
                )

            print(f"[SUCCESS] Model {versionDetails['CreationTimestamp']} is running!")
            return True
        elif versionDetails["Status"] == "STOPPING":
            return commons.respond(
                messageType="ERROR",
                message=f"{commons.GESTURE_RECOG_PROJECT_NAME} is stopping. Please check again later when the process is not busy...",
                code=23
            )
        elif versionDetails["Status"] == "STARTING":
            return commons.respond(
                messageType="ERROR",
                message=f"{commons.GESTURE_RECOG_PROJECT_NAME} is starting. Please check again later when the process is complete...",
                code=23
            )
        else:
            # Model is already running
            print(f"[SUCCESS] The latest model (created at {versionDetails['CreationTimestamp']} is already running!")
            return True

    # Stop the model after recog is complete
    else:
        if (versionDetails["Status"] == "RUNNING"):
            print(f"[INFO] Stopping latest {commons.GESTURE_RECOG_PROJECT_NAME} model...")
            try:
                rekogClient.stop_project_version(
                    ProjectVersionArn=os.getenv("LATEST_MODEL_ARN")
                )
            except Exception as e:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Failed to stop the latest model of {commons.GESTURE_RECOG_PROJECT_NAME}",
                    content={ "ERROR" : str(e) },
                    code=15
                )

            # Verify model was actually stopped
            stoppingVersion = getProjectVersions()[0]
            if stoppingVersion["Status"] != "RUNNING":
                # Stopping a model takes less time than starting one
                stopTimeout = 150
                print(f"[INFO] Request to stop {commons.GESTURE_RECOG_PROJECT_NAME} model was successfully sent! Waiting {stopTimeout}s for the model to stop...")
                time.sleep(stopTimeout)
                stoppedVersion = getProjectVersions()[0]

                if stoppedVersion["Status"] == "STOPPED":
                    print(f"[SUCCESS] {commons.GESTURE_RECOG_PROJECT_NAME} model was successfully stopped!")
                    return True
                else:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"{commons.GESTURE_RECOG_PROJECT_NAME} FAILED to stop properly before {stopTimeout}s timeout expired",
                        content={ "STATUS" : stoppedVersion["Status"] },
                        code=15
                    )
            else:
                return commons.respond(
                    messageType="ERROR",
                    message=f"{commons.GESTURE_RECOG_PROJECT_NAME} stop request was successfull but the latest model is still running.",
                    content={ "MODEL" :  stoppingVersion['CreationTimestamp'], "STATUS" : stoppingVersion['Status'] },
                    code=1
                )
        elif versionDetails["Status"] == "STARTING":
            return commons.respond(
                messageType="ERROR",
                message=f"{commons.GESTURE_RECOG_PROJECT_NAME} is starting. Please check again later when the process is not busy...",
                code=23
            )
        elif versionDetails["Status"] == "STOPPING":
            return commons.respond(
                messageType="ERROR",
                message=f"{commons.GESTURE_RECOG_PROJECT_NAME} is stopping. Please check again later when the process is complete...",
                code=23
            )
        else:
            print(f"[WARNING] {commons.GESTURE_RECOG_PROJECT_NAME} model is already stopped!")
            return True

def main(argv):
    """main() : Main method that parses the input opts and returns the result"""
    # Parse input parameters
    argumentParser = argparse.ArgumentParser(
        description="Runs gesture recognition of an image or video frame against an image and has the option of exapnding it to check if a specific user possesses said gesture",
        formatter_class=argparse.RawTextHelpFormatter
    )
    argumentParser.add_argument("-a", "--action",
        required=True,
        choices=["gesture", "start", "stop"],
        help="""Only one action can be performed at one time:\n\gesture: Runs gesture recognition analysis against a set of images (paths seperated by spaces).\n\start: Starts the rekognition project\n\stop: Stops the rekognition project.
        """
    )
    argumentParser.add_argument("-f", "--files",
        required=False,
        action="extend",
        nargs="+",
        help="List of full paths (seperated by spaces) to a gesture combination (in order) that you would like to analyse."
    )
    argumentParser.add_argument("-m", "--maintain",
        action="store_true",
        required=False,
        help="If this parameter is set, the gesture recognition project will not be closed after rekognition is complete (only applicable with -a gesture"
    )
    argDict = argumentParser.parse_args()

    if argDict.action == "gesture":
        # Start Rekog project
        projectHandler(True)

        # Iterate through given images
        foundGestures = []
        try:
            for imagePath in argDict.files:
                # We will always be using a local file (or it's file bytes) so no need to check if in s3 or not here
                if os.path.isfile(imagePath):
                    try:
                        Image.open(imagePath)
                    except IOError:
                        return commons.respond(
                            messageType="ERROR",
                            message=f"File {imagePath} exists but is not an image. Only jpg and png files are valid",
                            code=7
                        )
                    foundGesture = checkForGestures(imagePath)

                    # We have found a gesture
                    if foundGesture is not None:
                        foundGestures.append({ f"{imagePath}" : foundGesture })
                        continue
                    else:
                        print(f"[WARNING] No gesture was found within {imagePath} (Available gestures = {' '.join(getGestureTypes())})")
                else:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"No such file {argDict.file}",
                        code=8
                    )
        finally:
            if argDict.maintain is False:
                projectHandler(False)

        # Display results
        if foundGestures == []:
            return commons.respond(
                messageType="ERROR",
                message=f"No gestures were found within the images",
                content={ "GESTURES" : foundGestures },
                code=17
            )
        else:
            return commons.respond(
                messageType="SUCCESS",
                message=f"Found gestures!",
                content={ "GESTURES" : foundGestures },
                code=0
            )

    elif argDict.action == "start":
        projectHandler(True)
        return commons.respond(
            messageType="SUCCESS",
            message="Latest project model is now running!",
            code=0
        )
    elif argDict.action == "stop":
        projectHandler(False)
        return commons.respond(
            messageType="SUCCESS",
            message="Latest project model is now stopped!",
            code=0
        )
    else:
        return commons.respond(
            messageType="ERROR",
            message=f"Invalid action type - {argDict.action}",
            code=13
        )

if __name__ == "__main__":
    main(sys.argv[1:])