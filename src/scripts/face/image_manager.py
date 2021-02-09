# -----------------------------------------------------------
# Uploads an image containing a face to S3
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

import boto3
from botocore.exceptions import ClientError

import argparse
import os
from PIL import Image

import sys
sys.path.append(os.path.dirname(__file__) + "/..")
import index_photo
import compare_faces
import commons

client = boto3.client('s3')

def delete_file(fileName):
    """delete_file() : Deletes a S3 object file
    :param fileName: S3 Path to file to be deleted
    """

    client.delete_object(
        Bucket = commons.FACE_RECOG_BUCKET,
        Key = fileName
    )

    # Verify the object was deleted
    try:
        deletionRequest = client.get_object_acl(
            Bucket = commons.FACE_RECOG_BUCKET,
            Key = fileName
        )

        commons.throw("ERROR", f"Failed to delete {fileName}. Deletion response:\n{deletionRequest}", 2)
    except client.exceptions.NoSuchKey:
        print(f"[SUCCESS] {fileName} has been successfully deleted from S3!")

def upload_file(fileName, s3Name=None):
    """upload_file() : Uploads a file to an S3 bucket based off the input params entered.
    :param fileName: Path to file to be uploaded
    :param s3Name: S3 object name and or path. If not specified then the filename is used
    """

    # If S3 name was not specified, use fileName
    if s3Name is None:
        objectName = commons.parseObjectName(fileName)
    else:
        objectName = commons.parseImageObject(s3Name)

    objectName = f"users/{objectName}"

    print(f"[INFO] S3 Object Path will be {objectName}")

    # Upload the file
    try:
        with open(fileName, "rb") as fileBytes:
            response = client.upload_fileobj(
                Fileobj = fileBytes,
                Bucket = commons.FACE_RECOG_BUCKET,
                Key = objectName
            )
    except ClientError as e:
        commons.throw("ERROR", f"{fileName} FAILED to upload to S3\n{e}", 1)

    print(f"[SUCCESS] {objectName} has been uploaded to {commons.FACE_RECOG_BUCKET}")

    return objectName

#########
# START #
#########
def main(argv):
    """main() : Main method that parses the input opts and returns the result"""

    # Parse input parameters
    argumentParser = argparse.ArgumentParser(
        description="S3 image manager. Allows for the creation or deletion of images inside S3.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    argumentParser.add_argument("-a", "--action",
        required=True,
        choices=["create", "delete"],
        help="""Action to be conducted on the --file. Only one action can be performed at one time:\n\ncreate: Uploads the --file to S3 and indexes it (if --index is present). --name can optionally be added if the name of the --file is not what it should be in S3.\n\ndelete: Deletes the --file inside S3.\n\nNote: There is no edit/rename action as S3 doesn't offer object renaming or deletion. If you wish to rename an object, delete the original and create a new one.
        """
    )
    argumentParser.add_argument("-f", "--file",
        required=True,
        help="Full path to jpg or png image file to be manipulated in this operation."
    )
    argumentParser.add_argument("-n", "--name",
        required=False,
        help="S3 name of the image to be uploaded. This is what the image will be stored as in S3. If not specified, the filename passed to --file is used instead."
    )
    argumentParser.add_argument("-i", "--index",
        required=False,
        action="store_true",
        help="Index the image to the rekognition collection as soon as it's been uploaded"
    )
    argumentParser.add_argument("-c", "--compare",
        required=False,
        action="store_true",
        help="Run the comparison library to instantly check the stream for any user faces"
    )
    argDict = argumentParser.parse_args()

    # Ensure that the file to be uploaded is an existing photo
    if argDict.action == "create":
        if os.path.isfile(argDict.file):
            try:
                Image.open(argDict.file)
            except IOError:
                commons.throw("ERROR", f"File {argDict.file} exists but is not an image. Only jpg and png files are valid", 2)
        else:
            commons.throw("ERROR", f"No such file {argDict.file}", 3)

        uploadedImagePath = upload_file(argDict.file, argDict.name)

        # Immediately index the photo into a local collection if param is set
        if argDict.index == True:
            print(f"[INFO] Indexing photo into {commons.FACE_RECOG_COLLECTION}")
            index_photo.add_face_to_collection(uploadedImagePath)

    # Ensure the file to be edited or deleted exists. Then, delete it from both the collection and S3 (if needs be)
    elif argDict.action == "delete":

        # Immediately delete the photo from local collection if param is set
        if argDict.index == True:
            print(f"[INFO] Removing photo from {commons.FACE_RECOG_COLLECTION}")
            index_photo.remove_face_from_collection(argDict.file)

        s3FilePath = f"users/{argDict.file}"

        try:
            client.get_object_acl(
                Bucket = commons.FACE_RECOG_BUCKET,
                Key = s3FilePath
            )
        except client.exceptions.NoSuchKey:
            commons.throw("ERROR", f"No such file {s3FilePath} exists in S3.", 3)

        delete_file(s3FilePath)

    else:
        commons.throw("ERROR", f"Invalid action type - {argDict.action}", 2)

    # Run comparison on stream
    if argDict.compare == True:
        print("[INFO] Running comparison library to check for user faces in current stream...")
        compare_faces.checkForFaces()

if __name__ == "__main__":
    main(sys.argv[1:])
