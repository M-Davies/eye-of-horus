# -----------------------------------------------------------
# Retrieves a photo from S3 or locally and adds it to a Rekognition Collection
#
# Copyright (c) 2021 Morgan Davies, UK
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

client = boto3.client('rekognition')

def remove_face_from_collection(imagePath):
    """remove_face_from_collection() : Removes a face from the rekognition collection.
    :param imagePath: External image id to be deleted
    """

    # Verify face exists in collection
    faces = client.list_faces(
        CollectionId = commons.FACE_RECOG_COLLECTION,
    )

    foundFace = False
    for face in faces["Faces"]:
        if imagePath == face["ExternalImageId"]:
            print(f"[INFO] {imagePath} found with object name {imagePath} : {face['FaceId']}. Face to be deleted:\n{face}")
            foundFace = face['FaceId']
            break

    if foundFace == False:
        commons.throw("ERROR", f"No face found in collection with object name {imagePath}", 2)

    # Delete Object
    deletedResponse = client.delete_faces(
        CollectionId = commons.FACE_RECOG_COLLECTION,
        FaceIds = [foundFace]
    )

    # Verify face was deleted
    if deletedResponse["DeletedFaces"][0] != foundFace:
        commons.throw("ERROR", f"Failed to delete face with id {foundFace}. Face ID {deletedResponse['DeletedFaces'][0]} was deleted instead.", 4)

    print(f"[SUCCESS] {imagePath} was successfully removed from {commons.FACE_RECOG_COLLECTION}!")

def add_face_to_collection(imagePath, s3Name=None):
    """add_face_to_collection() : Retrieves an image and indexes it to a rekognition collection, ready for examination.
    :param imagePath: Path to file to be uploaded
    :param objectName: S3 object name and or path. If not specified then file_name is used
    """

    # If an objectName was not specified, use file_name
    if s3Name is None:
        objectName = commons.parseObjectName(imagePath)
    else:
        objectName = commons.parseImageObject(s3Name)

    # Check if we're using a local file
    if os.path.isfile(imagePath):
        try:
            Image.open(imagePath)
        except IOError:
            commons.throw("ERROR", f"File {imagePath} exists but is not an image. Only jpg and png files are valid", 7)

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

    print(f"[SUCCESS] Face successfully indexed! Dumping metadata...")
    for faceRecord in response['FaceRecords']:
         print(json.dumps(faceRecord, indent=2))

#########
# START #
#########
def main(argv):
    """main() : Main method that parses the input opts and returns the result"""

    # Parse input parameters
    argumentParser = argparse.ArgumentParser(
        description="Adds a face from S3 or local drive to a rekognition collection",
        formatter_class=argparse.RawTextHelpFormatter
    )
    argumentParser.add_argument("-a", "--action",
        required=True,
        choices=["add", "delete"],
        help="""Action to be conducted on the --file. Only one action can be performed at one time:\n\nadd: Adds the --file to the collection. --name can optionally be added if the name of the --file is not what it should be in S3.\n\ndelete: Deletes the --file inside the collection.\n\nNote: There is no edit/rename action as collections don't support image renaming or deletion. If you wish to rename an image, delete the original and create a new one.
        """
    )
    argumentParser.add_argument("-f", "--file",
        required=True,
        help="Full path to a jpg or png image file (s3 or local)"
    )
    argumentParser.add_argument("-n", "--name",
        required=False,
        help="ID that the image will have inside the collection. If not specified then the filename is used"
    )
    argDict = argumentParser.parse_args()

    if argDict.action == "delete":
        remove_face_from_collection(argDict.file)
    else:
        add_face_to_collection(argDict.file, argDict.name)

if __name__ == "__main__":
    main(sys.argv[1:])
