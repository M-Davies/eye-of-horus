# -----------------------------------------------------------
# Compares a face from the stream with a face in the index to check for a valid face
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

import boto3
rekog = boto3.client("rekognition")
kinesis = boto3.client("kinesis")
knVideo = boto3.client("kinesisvideo")

from dotenv import load_dotenv
load_dotenv()

import os
import argparse
import json

import sys
sys.path.append(os.path.dirname(__file__) + "/..")
import commons

def createProcessor():
    """createProcessor() : Creates a stream processor.
    We assume that the kinesis video and data streams have already been created using the console.
    The default FaceMatchThreshold has been increased since testing has shown it to be quicker at this level.
    """
    rekog.create_stream_processor(
        Input={
            "KinesisVideoStream": {
                "Arn": knVideo.describe_stream(StreamName=commons.CAMERA_STREAM_NAME)["StreamInfo"]["StreamARN"]
            }
        },
        Output={
            "KinesisDataStream": {
                "Arn": kinesis.describe_stream(StreamName=commons.CAMERA_DATASTREAM_NAME)["StreamDescription"]["StreamARN"]
            }
        },
        Name=commons.FACE_RECOG_PROCESSOR,
        Settings={
            "FaceSearch": {
                "CollectionId": commons.FACE_RECOG_COLLECTION,
                "FaceMatchThreshold": 90
            }
        },
        RoleArn=os.getenv("ROLE_ARN")
    )

    # Once it has been created, this should now pass without a ResourceNotFoundException
    return rekog.describe_stream_processor(Name = commons.FACE_RECOG_PROCESSOR)

#########
# START #
#########
def checkForFaces():
    """checkForFaces() : Main method that handles all interactions with the stream and indicies. Note: this package is not supposed to be run directly, it should be instantiated from image_manager.py"""

    # Create & Start/Restart Stream Processer if it hasn"t been already
    try:
        processor = rekog.describe_stream_processor(
            Name = commons.FACE_RECOG_PROCESSOR
        )
    except rekog.exceptions.ResourceNotFoundException:
        commons.throw("WARNING", f"{commons.FACE_RECOG_PROCESSOR} does not appear to exist. Creating now")
        processor = createProcessor()
    print(f"[SUCCESS] {commons.FACE_RECOG_PROCESSOR} has been successfully created!")

    if processor["Status"] != "RUNNING":
        print(f"[INFO] Starting Rekognition Stream Processor {commons.FACE_RECOG_PROCESSOR}...")
        rekog.start_stream_processor(
            Name = commons.FACE_RECOG_PROCESSOR
        )
    else:
        print(f"[SUCCESS] {commons.FACE_RECOG_PROCESSOR} is already running!")
    
    





