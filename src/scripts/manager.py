# -----------------------------------------------------------
# Uploads an image containing a face to S3
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# -----------------------------------------------------------

import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError

import cv2
import sys
import argparse
import os
import time
import subprocess
import signal
from PIL import Image

from face import index_photo
from face import compare_faces
from gesture import gesture_recog
import commons

client = boto3.client('s3')

def delete_file(fileName):
    """delete_file() : Deletes a S3 object file
    :param fileName: S3 Path to file to be deleted
    """

    try:
        client.delete_object(
            Bucket = commons.FACE_RECOG_BUCKET,
            Key = fileName
        )
    except EndpointConnectionError:
        commons.respond(
            messageType="ERROR",
            message="FAILED to delete object from S3. Could not establish a connection to AWS",
            code=3
        )

    # Verify the object was deleted
    try:
        deletionRequest = client.get_object_acl(
            Bucket = commons.FACE_RECOG_BUCKET,
            Key = fileName
        )
    except client.exceptions.NoSuchKey:
        print(f"[SUCCESS] {fileName} has been successfully deleted from S3!")
        return fileName
    except EndpointConnectionError:
        commons.respond(
            messageType="ERROR",
            message="FAILED to verify if object was successfully deleted from S3. Could not establish a connection to AWS",
            code=2
        )

    commons.respond(
        messageType="ERROR",
        message=f"Failed to delete {fileName}",
        content={ "ERROR" : deletionRequest },
        code=4
    )

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
        commons.respond(
            messageType="ERROR",
            message=f"{fileName} FAILED to upload to S3",
            content={ "ERROR" : e },
            code=3
        )
    except EndpointConnectionError:
        commons.respond(
            messageType="ERROR",
            message="FAILED to upload to S3. Could not establish a connection to AWS",
            code=3
        )

    return objectName

def streamHandler(start):
    """streamHandler() : Starts the live stream to AWS, contained within a finally block that will execute on function completion.
    :param start: Boolean denoting whether we are starting or stopping the stream
    """
    if start:
        # Boot up live stream
        startStreamRet = subprocess.call("./startStream.sh", close_fds=True)
        if startStreamRet != 0:
            commons.respond(
                messageType="ERROR",
                message=f"Stream failed to start (see CONTENT field for error code), see log for details",
                content={ "ERROR" : startStreamRet },
                code=5
            )
        else:
            # We have to sleep for a bit here as the steam takes ~3s to boot
            time.sleep(3)
    else:
        # Terminate streaming and reset signal handler everytime
        stopStreamRet = subprocess.call("./stopStream.sh")

        if stopStreamRet != 0:
            commons.respond(
                messageType="ERROR",
                message=f"Stream failed to die (see CONTENT field for error code), see log for details",
                content={ "ERROR" : stopStreamRet },
                code=6
            )

def timeoutHandler(signum, stackFrame):
    """timeoutHandler() : Raises a TimeoutError when the signal alarm goes off.
    :param signum: Signal handler caller number
    :param stackFrame: Current stack frame object where it was aborted
    """
    raise TimeoutError

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
        choices=["create", "delete", "compare", "gesture"],
        help="""Action to be conducted on the --file. Only one action can be performed at one time:\n\ncreate: Uploads the --file to S3 and indexes it (if --index is present). --name can optionally be added if the name of the --file is not what it should be in S3.\n\ndelete: Deletes the --file inside S3.\n\ncompare: Executes the facial comparison library against ALL users in the database.\n\ngesture: Executes the gesture comparison library against the logged in user.\n\nNote: There is no edit/rename action as S3 doesn't offer object renaming or deletion. If you wish to rename an object, delete the original and create a new one.
        """
    )
    argumentParser.add_argument("-f", "--file",
        required=False,
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
    timeoutSeconds = 20
    argumentParser.add_argument("-t", "--timeout",
        required=False,
        type=int,
        help=f"Timeout (in seconds) for the stream to timeout after not finding a face or gesture during comparison\nUsed with -a compare or -a gesture, default is {timeoutSeconds}"
    )
    argumentParser.add_argument("-u", "--username",
        required=False,
        help="Username to retrieve the gestures from AWS for comparison with the gestures performed on the stream\nUsed with -a gesture"
    )
    argDict = argumentParser.parse_args()
    print("[INFO] Parsed arguments:")
    print(argDict)

    # Ensure that the file to be uploaded is an existing photo
    if argDict.action == "create":
        if os.path.isfile(argDict.file):
            try:
                Image.open(argDict.file)
            except IOError:
                commons.respond(
                    messageType="ERROR",
                    message=f"File {argDict.file} exists but is not an image. Only jpg and png files are valid",
                    code=7
                )
        else:
            commons.respond(
                messageType="ERROR",
                message=f"No such file {argDict.file}",
                code=8
            )

        uploadedImage = upload_file(argDict.file, argDict.name)

        # Immediately index the photo into a local collection if param is set
        if argDict.index == True:
            print(f"[INFO] Indexing photo into {commons.FACE_RECOG_COLLECTION}")
            indexedImage = index_photo.add_face_to_collection(uploadedImage)
            return commons.respond(
                messageType="SUCCESS",
                message=f"{uploadedImage} successfully uploaded to S3 and indexed into the Rekognition Collection.",
                content=indexedImage,
                code=0
            )
        else:
            return commons.respond(
                messageType="SUCCESS",
                message=f"{uploadedImage} was successfully uploaded to S3 (not indexed). Specify -i to index into the Rekognition client.",
                code=0
            )

    # Ensure the file to be edited or deleted exists. Then, delete it from both the collection and S3 (if needs be)
    elif argDict.action == "delete":

        # Immediately delete the photo from local collection if param is set
        if argDict.index == True:
            print(f"[INFO] Removing photo from {commons.FACE_RECOG_COLLECTION}")
            deletedFace = index_photo.remove_face_from_collection(argDict.file)

        s3FilePath = f"users/{argDict.file}"

        try:
            client.get_object_acl(
                Bucket = commons.FACE_RECOG_BUCKET,
                Key = s3FilePath
            )
        except client.exceptions.NoSuchKey:
            commons.respond(
                messageType="ERROR",
                message=f"No such file {s3FilePath} exists in S3.",
                code=9
            )

        deletedFilename = delete_file(s3FilePath)

        if argDict.index == True:
            return commons.respond(
                messageType="SUCCESS",
                message=f"{deletedFilename} was successfully removed from S3 and the Rekognition Collection.",
                content=deletedFace,
                code=0
            )
        else:
            return commons.respond(
                messageType="SUCCESS",
                message=f"{deletedFilename} was successfully removed from S3 but not from the Rekognition Collection. Please specify -i if you wish to remove the image from the collection too.",
                code=0
            )

    # Run comparison on stream
    elif argDict.action == "compare":
        if argDict.timeout != None:
            timeoutSeconds = argDict.timeout

        print(f"[INFO] Running facial comparison library to check for user faces in current stream (timing out after {timeoutSeconds}s)...")

        # Start/end stream
        streamHandler(True)

        # Start comparing, timing out if no face is found within the limit
        try:
            signal.signal(signal.SIGALRM, timeoutHandler)
            signal.alarm(timeoutSeconds)
            matchedFace = compare_faces.checkForFaces()

            # By this point, we have found a face so cancel the timeout and return the matched face
            signal.alarm(0)
            return commons.respond(
                messageType="SUCCESS",
                message=f"Found a matching face!",
                content=matchedFace,
                code=0
            )
        except TimeoutError:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            commons.respond(
                messageType="ERROR",
                message=f"TIMEOUT FIRED AFTER {timeoutSeconds}s, NO FACES WERE FOUND IN THE STREAM!",
                code=10
            )
        finally:
            # Reset signal handler everytime
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            streamHandler(False)

    # Run gesture recognition lib
    elif argDict.action == "gesture":
        if argDict.timeout != None:
            timeoutSeconds = argDict.timeout
        else:
            # Set a higher default timeout for gesture recog as it will take longer
            timeoutSeconds = 40
        print(f"[INFO] Running gesture recognition library to check for the correct gestures performed in current stream (timing out after {timeoutSeconds}s)...")

        # Start/end stream
        streamHandler(True)

        # Retrieve stream's session url endpoint
        kvClient = boto3.client('kinesisvideo')
        endpoint = kvClient.get_data_endpoint(
            StreamName = commons.CAMERA_STREAM_NAME,
            APIName = "GET_HLS_STREAMING_SESSION_URL"
        )["DataEndpoint"]

        # Grab the HLS Stream URL from the endpoint
        kvmClient = boto3.client("kinesis-video-archived-media", endpoint_url = endpoint)
        try:
            # Get live stream (only works if stream is active)
            streamUrl = kvmClient.get_hls_streaming_session_url(
                StreamName = commons.CAMERA_STREAM_NAME,
                PlaybackMode = "LIVE"
            )["HLSStreamingSessionURL"]

        except kvmClient.exceptions.ResourceNotFoundException:
            commons.respond(
                messageType="ERROR",
                messsage=f"Stream URL was not valid or stream wasn't found. Try restarting the stream and trying again",
                code=11
            )

        # Start checking for a matching gesture, timing out if the correct sequence is not found within the limit
        vcap = cv2.VideoCapture(streamUrl)
        try:
            signal.signal(signal.SIGALRM, timeoutHandler)
            signal.alarm(timeoutSeconds)

            matchedGestures = False
            while(matchedGestures is False):

                # Capture frame-by-frame
                ret, frame = vcap.read()

                if ret is not False or frame is not None:
                    # Run gesture recog lib against captured frame
                    matchedGestures = gesture_recog.checkForGestures(frame, argDict.username)
                else:
                    commons.respond(
                        messageType="ERROR",
                        message="Stream Interrupted or corrupted!",
                        code=12
                    )
                    break

            # By this point, we have found a set of matching gestures so cancel timeout and return access granted
            signal.alarm(0)
            print(f"[SUCCESS] Matched gesture combination for user {argDict.username}!")

        except TimeoutError:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            commons.respond(
                messageType="ERROR",
                message=f"TIMEOUT FIRED AFTER {timeoutSeconds}s, NO GESTURES WERE FOUND IN THE STREAM!",
                code=10
            )
        finally:
            # Reset signal handler everytime
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            streamHandler(False)

            # When everything done, release the capture
            vcap.release()
            cv2.destroyAllWindows()

    else:
        commons.respond(
            messageType="ERROR",
            message=f"Invalid action type - {argDict.action}",
            code=13
        )

if __name__ == "__main__":
    main(sys.argv[1:])
