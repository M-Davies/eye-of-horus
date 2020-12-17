# -----------------------------------------------------------
# Uploads an image containing a face to S3
#
# Copyright (c) 2020 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

import boto3
from botocore.exceptions import ClientError

import argparse
import os
from PIL import Image

import sys
sys.path.append(os.path.dirname(__file__) + "/..")
import commons

USAGE_STRING = "python facial_recognition.py -i <full_path_to_photo_file> -n <object_name>"

def upload_file(fileName, objectName=None):
    """upload_file() : Uploads a file to an S3 bucket based off the input params entered.
    :param fileName: Path to file to be uploaded
    :param objectName: S3 object name and or path. If not specified then the filename is used
    """

    # If S3 objectName was not specified, use fileName
    if objectName is None:
        objectName = commons.parseObjectName(fileName)

    print(f"[INFO] S3 Object Path will be {objectName}")

    # Upload the file
    client = boto3.client('s3')
    try:
        with open(fileName, "rb") as fileBytes:
            response = client.upload_fileobj(fileBytes, commons.FACE_RECOG_BUCKET, objectName)
    except ClientError as e:
        commons.throw("ERROR", f"{fileName} FAILED to upload to S3\n{e}", 1)

    print(f"[SUCCESS] {objectName} has been uploaded to {commons.FACE_RECOG_BUCKET}")

#########
# START #
#########
def main(argv):
    """main() : Main method that parses the input opts and returns the result from upload_file()"""

    # Parse input params
    # photoPath = None
    # objectName = None
    # index = False

    # fileOpt, objectOpt, indexOpt = False

    # Parse input parameters
    argumentParser = argparse.ArgumentParser(description="Uploads an image containing a face to S3")
    argumentParser.add_argument("-f", "--file",
        required=True,
        help="Full path to jpg or png image file to be uploaded"
    )
    argumentParser.add_argument("-n", "--name",
        required=False,
        help="S3 namepath of the image to be uploaded. Basically, this is what and where the image will be stored in S3"
    )
    argumentParser.add_argument("-i", "--index",
        required=False,
        action="store_true",
        help="Index the image to the rekognition collection as soon as it's been uploaded"
    )
    argDict = argumentParser.parse_args()

    # Ensure that the file is an existing photo
    if os.path.isfile(argDict.file):
        try:
            Image.open(argDict.file)
        except IOError:
            commons.throw("ERROR", f"File {argDict.file} exists but is not an image. Only jpg and png files are valid", 1)
    else:
        commons.throw("ERROR", f"No such file {argDict.file}", 3)

    upload_file(argDict.file, argDict.name)
    # try:
    #     opts, args = getopt.getopt(
    #         argv,
    #         "f:ni",
    #         ["file=", "name=", "index"]
    #     )
    # except getopt.GetoptError:
    #     commons.throw("ERROR", f"Unrecognised opt!\n[USAGE] {USAGE_STRING}", 2)

    # for opt, arg in filteredOpts:
    #     print(f"[INFO] Parsing Opt {opt} : {arg}")

    #     if opt in ("-f", "--file"):
    #         # Only one opt allowed of this type
    #         if fileOpt:
    #             commons.throw("WARNING", f"Duplicates of {opt} are not supported. Ignoring {arg}")
    #             continue

    #         # Ensure that the file is an existing photo
    #         if os.path.isfile(arg):
    #             try:
    #                 Image.open(arg)
    #                 photoPath = arg
    #             except IOError:
    #                 commons.throw("ERROR", f"File {arg} exists but is not an image. Only jpg and png files are valid", 1)
    #         else:
    #             commons.throw("ERROR", f"No such file {arg}", 3)

    #     elif opt in ("-n", "--name"):
    #         if objectOpt:
    #             commons.throw("WARNING", f"Duplicates of {opt} are not supported. Ignoring {arg}")
    #             continue

    #         objectName = arg

    #     elif opt in ("i", "--index"):
    #         if indexOpt:
    #             commons.throw("WARNING", f"Duplicates of {opt} are not supported. Ignoring {arg}")
    #             continue

    #         index = True

    #     else:
    #         commons.throw("ERROR", f"Unhandled parameter {opt} : {arg}", 2)

    # upload_file(photoPath, objectName)

    # Immediately index the photo into a local collection if param is set
    if argDict.index == True:
        print(f"[INFO] Immediatly indexing the photo into {commons.FACE_RECOG_COLLECTION}")
        import index_photo
        index_photo

if __name__ == "__main__":
    main(sys.argv[1:])
