# -----------------------------------------------------------
# Retrieves a photo from S3 or locally and adds it to a Rekognition Collection
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
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

def faceInCollection(faceId):
    """faceInCollection() : Searches and returns a user face's details (by it's external image id) in the rekognition collection
    :param faceId: External image id to search for
    :returns: Matched rekognition collection object
    """
    faces = client.list_faces(
        CollectionId = commons.FACE_RECOG_COLLECTION,
    )['Faces']

    foundFace = {}
    for face in faces:
        if faceId == face["ExternalImageId"]:
            print(f"[INFO] {faceId} found with object name {faceId} (id = {face['FaceId']}). Face to be deleted:\n{face}")
            foundFace = dict(face)
            break

    return foundFace

def remove_face_from_collection(imageId):
    """remove_face_from_collection() : Removes a face from the rekognition collection.
    :param imageId: External image id to be deleted (e.g. morgan.jpg)
    :return: Face details object that was deleted from the collection
    """

    foundFace = faceInCollection(imageId)

    if foundFace == {}:
        # If no face was found, check to see if there is an alternative jpg or png file of the same name
        if "jpg" in imageId:
            altImageId = imageId.replace(".jpg", ".png")
        else:
            altImageId = imageId.replace(".png", ".jpg")

        print(f"[WARNING] No face found with {imageId} image id. Trying to find a {altImageId} id to delete...")
        foundFace = faceInCollection(altImageId)

        # Still no face was found. Item does not likely exist so we return and leave error handling to caller
        if foundFace == {}:
            return None

    # Delete Object
    deletedResponse = client.delete_faces(
        CollectionId = commons.FACE_RECOG_COLLECTION,
        FaceIds = [foundFace['FaceId']]
    )

    # Verify face was deleted
    if deletedResponse["DeletedFaces"][0] != foundFace['FaceId']:
        return commons.respond(
            messageType="ERROR",
            message=f"Failed to delete face with id {foundFace['FaceId']}. Face ID {deletedResponse['DeletedFaces'][0]} was deleted instead.",
            code=4
        )

    print(f"[SUCCESS] {imageId} was successfully removed from the collection!")
    return foundFace

def add_face_to_collection(imagePath, s3Name=None):
    """add_face_to_collection() : Retrieves an image and indexes it to a rekognition collection, ready for examination.
    :param imagePath: Path to file to be uploaded
    :param objectName: S3 object name and or path. If not specified then file_name is used
    :return: Face object details that were created
    """

    # If an objectName was not specified, use the file name
    if s3Name is None:
        objectName = commons.parseObjectName(imagePath)
    else:
        objectName = commons.parseImageObject(s3Name)

    # Check if we're using a local file
    if os.path.isfile(imagePath):
        try:
            Image.open(imagePath)
        except IOError:
            return commons.respond(
                messageType="ERROR",
                message=f"File {imagePath} exists but is not an image. Only jpg and png files are valid",
                code=7
            )

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
        print(f"[WARNING] {imagePath} does not exist as a local file. Attempting to retrieve the image using the same path from S3 with object name {objectName}")
        try:
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
        except client.exceptions.InvalidS3ObjectException:
            return commons.respond(
                messageType="ERROR",
                message=f"No such file found locally or in S3: {imagePath}",
                code=9
            )

    # We're only looking to return one face
    print(f"[SUCCESS] {imagePath} was successfully added to the collection with image id {objectName}")
    return json.dumps(response['FaceRecords'][0])

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
        help="Full path to a jpg or png image file (s3 or local) to add to collection OR (if deleting) the file or username of the face to delete"
    )
    argumentParser.add_argument("-n", "--name",
        required=False,
        help="ID that the image will have inside the collection. If not specified then the filename is used"
    )
    argDict = argumentParser.parse_args()

    if argDict.action == "delete":
        response = remove_face_from_collection(argDict.file)
        if response is not None:
            return commons.respond(
                messageType="SUCCESS",
                message=f"{argDict.file} was successfully removed from the Rekognition Collection",
                content=response,
                code=0
            )
        else:
            commons.respond(
                messageType="ERROR",
                message=f"No face found in collection with object name {argDict.file}",
                code=2
            )
    else:
        response = add_face_to_collection(argDict.file, argDict.name)
        return commons.respond(
            messageType="SUCCESS",
            message=f"{argDict.file} was added to the Rekognition Collection!",
            content=response,
            code=0
        )

if __name__ == "__main__":
    main(sys.argv[1:])
