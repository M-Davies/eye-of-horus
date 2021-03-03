# -----------------------------------------------------------
# Runs gesture recognition on the capture frame
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

import boto3
client = boto3.client('rekognition')

import sys
import os
import argparse

from PIL import Image

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(__file__) + "/..")
import commons

# TODO: Add comments to functions

def getProjectVersions():
    """getProjectVersions() : Retrieves all versions of the custom labels model. Often, we will only use the first/latest version as that is generally the most accurate and up-to-date
    :return: List of project version in chronological order (latest to oldest)
    """
    try:
        return client.describe_project_versions(
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

def checkForGestures(image, username):
    """checkForGestures() : Entry point for the manager, this sets up the latest rekognition model and runs AWS custom labels against the given image
    :param image: Locally stored image OR stream frame to scan for authentication gestures
    :param username: The user to retrieve the gesture unlock combination for
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
                client.start_project_version(
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

            waitHandler = client.get_waiter('project_version_running')
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
        print(f"[INFO] Beginning analysis of image for user {username}")



    # Stop the model after recog is complete
    finally:
        print(f"[INFO] Stopping latest {commons.GESTURE_RECOG_PROJECT_NAME} model...")

        try:
            response=client.stop_project_version(
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