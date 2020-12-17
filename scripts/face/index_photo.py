# -----------------------------------------------------------
# Retrieves a photo from S3 or locally and adds it to a Rekognition Collection
#
# Copyright (c) 2020 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

import boto3

import os
import argparse
import json
from PIL import Image

import sys
sys.path.append(os.path.dirname(__file__) + "/..")
import commons

def add_face_to_collection(imagePath, objectName=None):
    """add_face_to_collection() : Retrieves an image and indexes it to a rekognition collection, ready for examination.
    :param imagePath: Path to file to be uploaded
    :param objectName: S3 object name and or path. If not specified then file_name is used
    """

    client = boto3.client('rekognition')

    # If an objectName was not specified, use file_name
    if objectName is None:
        objectName = commons.parseObjectName(imagePath)


    # Check if we're using a local file
    if os.path.isfile(imagePath):
        try:
            Image.open(imagePath)
        except IOError:
            commons.throw("ERROR", f"File {imagePath} exists but is not an image. Only jpg and png files are valid", 1)

        with open(imagePath, "rb") as fileBytes:
            print(f"[INFO] Indexing local image {imagePath} with collection object name {objectName}")
            response = client.index_faces(
                CollectionId = commons.FACE_RECOG_COLLECTION,
                Image = { 'Bytes' : fileBytes.read() },
                ExternalImageId = objectName,
                MaxFaces = 1,
                QualityFilter = "AUTO",
                DetectionAttributes = ['ALL']
            )

    else:
        # Use an S3 object if no file was found at the image path given
        commons.throw("WARNING", f"{imagePath} does not exist as a local file. Attempting to retrieve the image using the same path from S3")

        print(f"[INFO] Indexing S3 image at {imagePath} with collection object name {objectName}")
        response = client.index_faces(
            CollectionId = commons.FACE_RECOG_COLLECTION,
            Image = { 'S3Object' : {
                'Bucket' : commons.FACE_RECOG_BUCKET,
                'Name' : imagePath
            } },
            ExternalImageId = objectName,
            MaxFaces = 1,
            QualityFilter = "AUTO",
            DetectionAttributes = ['ALL']
        )

    print(f"[SUCCESS] Face successfully indexed! Dumping metadata and exiting...")
    for faceRecord in response['FaceRecords']:
         print(json.dumps(faceRecord, indent=2))

#########
# START #
#########
def main(argv):
    """main() : Main method that parses the input opts and returns the result from add_faces_to_collection()"""

    # Parse input parameters
    argumentParser = argparse.ArgumentParser(description="Adds a face from S3 or local drive to a rekognition collection")
    argumentParser.add_argument("-f", "--file",
        required=True,
        help="Full path to a jpg or png image file (s3 or local) to be added to the rekognition collection"
    )
    argumentParser.add_argument("-n", "--name",
        required=False,
        help="ID that the image will have inside the collection. If not specified then the filename is used"
    )
    argDict = argumentParser.parse_args()

    indexed_faces_count = add_face_to_collection(argDict.file, argDict.name)

if __name__ == "__main__":
    main(sys.argv[1:])
