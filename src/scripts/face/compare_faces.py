# -----------------------------------------------------------
# Compares a face from the stream with a face in the index to check for a valid face
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# -----------------------------------------------------------

import boto3
import botocore
import os
import json
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(__file__) + "/..")
import commons  # noqa: E402,F401
import time  # noqa: E402

rekog = boto3.client("rekognition")
kinesis = boto3.client("kinesis")
knVideo = boto3.client("kinesisvideo")


def compareFaces(localImage, username):
    with open(localImage, "rb") as fileBytes:
        return rekog.compare_faces(
            SourceImage={
                'Bytes': fileBytes.read(),
            },
            TargetImage={
                'S3Object': {
                    'Bucket': os.getenv('FACE_RECOG_BUCKET'),
                    'Name': f"users/{username}/{username}.jpg"
                }
            },
            SimilarityThreshold=95,
            QualityFilter='AUTO'
        )


def examineFace(record):
    """
    examineFace() : Decode and parse the shard bytes to extract a high matching face object. Once found, verify it is a real face by comparing the landmarks
    :param record: Shard containing frames and fragment numbers
    :return: The matched face object with the highest similarity to the detected face or None if it is not a real face or no matches were found
    """
    jsonData = json.loads(record["Data"])
    matchedFaces = None
    try:
        # NOTE: This will only check one face in the stream. This is intentional as the system gets overly complex and insecure when more than one face is trying to authenticate.
        matchedFaces = jsonData["FaceSearchResponse"][0]["MatchedFaces"]
    except IndexError:
        return matchedFaces

    # If only one matched face was found, use that.
    if len(matchedFaces) == 1:
        sourceLandmarks = jsonData["FaceSearchResponse"][0]["Landmarks"]
        try:
            username = matchedFaces[0]['ExternalImageId'].split('.jpg')[0]
        except:
            username = matchedFaces[0]['ExternalImageId'].split('.png')[0]
        targetLandmarks = rekog.detect_faces(
            Image={'S3Object': {
                'Bucket': os.getenv('FACE_RECOG_BUCKET'),
                'Name': f"users/{username}/{username}.jpg"
            }}
        )["FaceDetails"][0]["Landmarks"]
        if checkPresentationAttack(sourceLandmarks, targetLandmarks, username) is False:
            return matchedFaces[0]
        else:
            return None
    # Find the greatest confident face if there is more than one
    elif len(matchedFaces) > 1:
        matchedFace = max(matchedFaces, key=lambda ev: ev["Similarity"])

        sourceLandmarks = jsonData["FaceSearchResponse"][0]["Landmarks"]
        try:
            username = matchedFace['ExternalImageId'].split('.jpg')[0]
        except:
            username = matchedFace['ExternalImageId'].split('.png')[0]
        targetLandmarks = rekog.detect_faces(
            Image={'S3Object': {
                'Bucket': os.getenv('FACE_RECOG_BUCKET'),
                'Name': f"users/{username}/{username}.jpg"
            }}
        )["FaceDetails"][0]["Landmarks"]
        if checkPresentationAttack(sourceLandmarks, targetLandmarks, username) is False:
            return matchedFace
        else:
            return None
    # Just return nothing if no faces were found
    else:
        return None


def createShardIterator(shardId):
    """
    createShardIterator() : Creates an interator that will allow searching through the shards. This will be called multiple times as shard iterators usually expire after 5mins

    See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kinesis.html#Kinesis.Client.get_shard_iterator
    :param shardId: ID of the shard to create an iterator for
    :return: The shard iterator ID
    """
    return kinesis.get_shard_iterator(
        StreamName=os.getenv('CAMERA_DATASTREAM_NAME'),
        ShardId=shardId,
        ShardIteratorType="LATEST"
    )["ShardIterator"]


def checkPresentationAttack(sourceLandmarks, targetLandmarks, user):
    """checkPresentationAttack() : Takes in two landmarks arrays and compares the key features to see if they are close enough to confirm the application is not being subjected to a presentation attack
    :param sourceLandmarks: Array of landmarks from the source image
    :param targetLandmarks: Array of landmarks from the target image
    :param user: User that is attempting to authenticate
    :return: True if an attack is occurring, false otherwise
    """
    for landmarkEntry in ["eyeLeft", "eyeRight", "nose", "mouthLeft", "mouthRight"]:
        # Get matching landmark in source and target
        sourceMark = next((item for item in sourceLandmarks if item['Type'] == landmarkEntry), None)
        if sourceMark is None: return True
        targetMark = next((item for item in targetLandmarks if item['Type'] == landmarkEntry), None)

        # Compare the positions of each within a certain threshold, fail if they are not within it
        if abs(round(sourceMark["X"], 2) - round(targetMark["X"], 2)) <= 0.1 is False or abs(round(sourceMark["Y"], 2) - round(targetMark["Y"], 2)) <= 0.1 is False:
            return True

    return False


def examineShard(shardJson):
    """
    examineShard() : Iterates through the latest shards obtained from the stream, retrieving the matched faces data for each shard
    :param shardJson: Details of the shard
    :return: The face that closest matches the detected face in the stream
    """
    iterator = createShardIterator(shardJson["ShardId"])
    faceFound = None

    while faceFound is None:
        try:
            # Get data from stream using the created iterator
            try:
                records = kinesis.get_records(
                    ShardIterator=iterator
                )
            except botocore.exceptions.HTTPClientError:
                # Special case as when the signal handler cancels the script during a get records, it will raise this exception
                raise TimeoutError

            # If records array empty, try adjacent shard and iterate until timeout expires or face is found
            if records["Records"] == []:
                print(f"[WARNING] No records were found in shard {shardJson['ShardId']}. Trying next shard with same iterator...")
                iterator = records['NextShardIterator']
                continue
            else:
                # Iterate through data records and see if there is a matching face. If there is, break loop
                for record in records["Records"]:
                    faceFound = examineFace(record)

                    if faceFound is not None:
                        break

        # API is being spammed. Sleep to let it recover
        except kinesis.exceptions.ProvisionedThroughputExceededException:
            print("[WARNING] Exceeded AWS API limit for get-records. Sleeping and trying again...")
            time.sleep(0.5)
        # Shard Iterator has expired.
        except kinesis.exceptions.ExpiredIteratorException:
            print("[WARNING] Shard iterator has expired. Creating a new one now...")
            iterator = createShardIterator(shardJson["ShardId"])

    return faceFound


#########
# START #
#########
def checkForFaces():
    """checkForFaces() : Main method that handles all interactions with the stream and indicies. Note: this package is not supposed to be run directly, it should be instantiated from image_manager.py"""

    # Create & Start/Restart Stream Processer if it hasn"t been already
    try:
        processor = rekog.describe_stream_processor(
            Name=os.getenv('FACE_RECOG_PROCESSOR')
        )
        print(f"[SUCCESS] {os.getenv('FACE_RECOG_PROCESSOR')} already exists")
    except rekog.exceptions.ResourceNotFoundException:
        print(f"[WARNING] {os.getenv('FACE_RECOG_PROCESSOR')} does not appear to exist. Creating now...")
        rekog.create_stream_processor(
            Input={
                "KinesisVideoStream": {
                    "Arn": knVideo.describe_stream(StreamName=os.getenv('CAMERA_STREAM_NAME'))["StreamInfo"]["StreamARN"]
                }
            },
            Output={
                "KinesisDataStream": {
                    "Arn": kinesis.describe_stream(StreamName=os.getenv('CAMERA_DATASTREAM_NAME'))["StreamDescription"]["StreamARN"]
                }
            },
            Name=os.getenv('FACE_RECOG_PROCESSOR'),
            Settings={
                "FaceSearch": {
                    "CollectionId": os.getenv('FACE_RECOG_COLLECTION'),
                    "FaceMatchThreshold": 95
                }
            },
            RoleArn=os.getenv("ROLE_ARN")
        )
        processor = rekog.describe_stream_processor(Name=os.getenv('FACE_RECOG_PROCESSOR'))
        print(f"[SUCCESS] {os.getenv('FACE_RECOG_PROCESSOR')} has been successfully created!")

    if processor["Status"] != "RUNNING":
        print(f"[INFO] Starting Rekognition Stream Processor {os.getenv('FACE_RECOG_PROCESSOR')}...")
        rekog.start_stream_processor(Name=os.getenv('FACE_RECOG_PROCESSOR'))
    else:
        print(f"[SUCCESS] {os.getenv('FACE_RECOG_PROCESSOR')} is already running")

    # Get latest shards
    shards = kinesis.list_shards(
        StreamName=os.getenv('CAMERA_DATASTREAM_NAME'),
        ShardFilter={
            "Type": "AT_LATEST"
        }
    )["Shards"]

    # Iterate through the shards
    for shard in shards:
        matchedFace = examineShard(shard)

    # We will always return a successfull face or be forcibly aborted by the manager timeout
    return matchedFace
