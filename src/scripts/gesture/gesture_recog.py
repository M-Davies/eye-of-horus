# -----------------------------------------------------------
# Runs gesture recognition on the capture frame to see if it contains a gesture. Will check if a user posses such a gesture in their pattern if so.
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# -----------------------------------------------------------

import boto3
rekogClient = boto3.client('rekognition')
s3Client = boto3.client('s3')

import sys
import os
import argparse

from PIL import Image

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(__file__) + "/..")
import commons

def inUserCombination(gestureJson, username, position):
    """inUserCombination() : Calculates if the given gesture is in the user's combination and in the correct position.
    :param gestureJson: Identified gesture JSON object returned from AWS detect_custom_labels
    :param username: User to pull gesture combination
    :param position: Position in the combination we are checking for the gestureJson
    :return: Boolean denoting if the given gesture and position are both valid in the user's gesture combination
    """

    # Retrieve user's gesture config file
    gestureConfig = s3Client.get_object(
        Bucket=commons.FACE_RECOG_BUCKET,
        Key=f"users/{username}"
    )

def analyseImage(image):
    """analyseImage() : Queries the latest AWS Custom Label model for the gesture metadata. I.e. Does this image contain a gesture and if so, which one is it most likely?
    :param image: Image/bytes to scan for gestures
    :return: JSON object containing the gesture with the highest confidence
    """
    try:
        with open(image, "rb") as fileBytes:
            detectedLabels = rekogClient.detect_custom_labels(
                Image={
                    'Bytes': fileBytes,
                },
                MinConfidence=70,
                ProjectVersionArn=os.getenv("LATEST_MODEL_ARN")
            )['CustomLabels']
    except OSError:
        print("[WARNING] Image file could not be found, it is likely we already have the image bytes...")
        detectedLabels = rekogClient.detect_custom_labels(
            Image={
                'Bytes': image,
            },
            MinConfidence=70,
            ProjectVersionArn=os.getenv("LATEST_MODEL_ARN")
        )['CustomLabels']

    # Extract gesture with highest confidence (return None if no gesture found)
    try:
        return max(detectedLabels, key = lambda ev: ev["Confidence"])
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
        commons.respond(
            messageType="ERROR",
            message="Failed to retrieve project version descriptions. Please check your internet connection and .env file.",
            content={ "ERROR" : e },
            code=2
        )

def checkForGestures(image):
    """checkForGestures() : Entry point for the manager, this sets up the latest rekognition model and runs AWS custom labels against the given image
    :param image: Locally stored image OR stream frame to scan for authentication gestures
    """
    # Verify that the latest rekognition model is running
    print(f"[INFO] Checking if {commons.GESTURE_RECOG_PROJECT_NAME} has already been started...")

    try:
        # Only bother retrieving the newest version
        versionDetails = getProjectVersions()[0]

        if (versionDetails["Status"] is not "RUNNING"):
            print(f"[WARNING] {commons.GESTURE_RECOG_PROJECT_NAME} is not running. Starting latest model for this project (created at {versionDetails['CreationTimestamp']}) now...")

            # Start it and wait to be in a usable state
            try:
                rekogClient.start_project_version(
                    ProjectVersionArn=os.getenv("LATEST_MODEL_ARN"),
                    MinInferenceUnits=1 # Stick to one unit to save money
                )
            except Exception as e:
                commons.respond(
                    messageType="ERROR",
                    message=f"Failed to start {commons.GESTURE_RECOG_PROJECT_NAME}.",
                    content={ "ERROR" : e },
                    code=14
                )

            print(f"[INFO] {commons.GESTURE_RECOG_PROJECT_NAME} has been started. Waiting for confirmation from AWS...")

            waitHandler = rekogClient.get_waiter('project_version_running')
            # Check every 5 seconds for 1min to get it done quick
            try:
                waitHandler.wait(
                    ProjectArn=os.getenv("PROJECT_ARN"),
                    WaiterConfig={
                        "Delay" : 5,
                        "MaxAttempts" : 12
                    }
                )
            except Exception as e:
                commons.respond(
                    messageType="ERROR",
                    message=f"{commons.GESTURE_RECOG_PROJECT_NAME} FAILED to start properly within 1min",
                    content={ "ERROR" : e },
                    code=15
                )

            print(f"[SUCCESS] Model {versionDetails['CreationTimestamp']} is running!")
        else:
            # Model is already running (unlikely but possible if the finally statement failed)
            print(f"[SUCCESS] The latest model (created at {versionDetails['CreationTimestamp']} is already running!")

        # Analyse the given image
        print(f"[INFO] Beginning analysis of image to see if it contains a gesture...")
        analysisResponse = analyseImage(image)

        if analysisResponse is not None:
            commons.respond(
                messageType="SUCCESS",
                message=f"Found a gesture for image!",
                content=analysisResponse,
                code=0
            )
            return analysisResponse
        else:
            commons.respond(
                messageType="WARNING",
                message=f"No gesture was detected in image!",
                code=0
            )

    # Stop the model after recog is complete
    finally:
        print(f"[INFO] Stopping latest {commons.GESTURE_RECOG_PROJECT_NAME} model...")

        try:
            rekogClient.stop_project_version(
                ProjectVersionArn=os.getenv("LATEST_MODEL_ARN")
            )
        except Exception as e:
            commons.respond(
                messageType="ERROR",
                message=f"Failed to stop the latest model of {commons.GESTURE_RECOG_PROJECT_NAME}",
                content={ "ERROR" : e },
                code=15
            )

        # Verify model was actually stopped
        stoppedModel = getProjectVersions()[0]
        if stoppedModel["Status"] is not "RUNNING":
            print(f"[SUCCESS] {commons.GESTURE_RECOG_PROJECT_NAME} model was successfully stopped!")
        else:
            commons.respond(
                messageType="ERROR",
                message=f"{commons.GESTURE_RECOG_PROJECT_NAME} stop request was successfull but the latest model is still running.",
                content={ "MODEL" :  stoppedModel['CreationTimestamp'], "STATUS" : stoppedModel['Status'] },
                code=1
            )

def main(argv):
    """main() : Main method that parses the input opts and returns the result"""
    # Parse input parameters
    argumentParser = argparse.ArgumentParser(
        description="Runs gesture recognition of an image or video frame against an image and has the option of exapnding it to check if a specific user possesses said gesture",
        formatter_class=argparse.RawTextHelpFormatter
    )
    argumentParser.add_argument("-f", "--files",
        required=True,
        action="extend",
        nargs="+",
        help="List of full paths (seperated by spaces) to a JPG or PNG image file that contain a gesture you would like to evaluate"
    )
    argumentParser.add_argument("-u", "--username",
        required=False,
        help="Username to retrieve the gestures from AWS for comparison with the gestures performed in the image. This is optional, you may opt out of this param if you only wish to check if your image contains a supported gesture."
    )
    argDict = argumentParser.parse_args()

    # Iterate through given images
    imageNum = 1
    for imagePath in argDict.files:
        # We will always be using a local file (or it's file bytes) so no need to check if in s3 or not here
        if os.path.isfile(imagePath):
            try:
                Image.open(imagePath)
            except IOError:
                commons.respond(
                    messageType="ERROR",
                    message=f"File {imagePath} exists but is not an image. Only jpg and png files are valid",
                    code=7
                )
            foundGesture = checkForGestures(imagePath)

            # We have found a gesture, let's see if the user has one that matches
            if argDict.username != None:
                print(f"[INFO] Checking if {argDict.username} contains the identified gesture...")
                userHasGesture = inUserCombination(foundGesture, argDict.username, imageNum)

                # User has gesture and it's at the right position
                if userHasGesture is True:
                    print(f"[SUCCESS] Correct gesture given for position {imageNum}! Checking next gesture...")
                    imageNum += 1
                else:
                    # TODO: Not sure if we should be printing this without using the commons lib
                    print(f"[WARNING] Image {imageNum} was not the right gesture or was in the wrong position in the user combination")
            else:
                return commons.respond(
                    messageType="SUCCESS",
                    message=f"Found a gesture within the target image!",
                    content=foundGesture,
                    code=0
                )
        else:
            commons.respond(
                messageType="ERROR",
                message=f"No such file {argDict.file}",
                code=8
            )

if __name__ == "__main__":
    main(sys.argv[1:])