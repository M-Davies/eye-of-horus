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

def upload_file(fileName, username, locktype=None, s3Name=None):
    """upload_file() : Uploads a file to an S3 bucket based off the input params entered.
    :param fileName: Path to file to be uploaded
    :param username: User to upload the new face details to
    :param s3Name: S3 object name and or path. If not specified then the filename is used
    """
    # Verify file exists
    if os.path.isfile(fileName):
        try:
            Image.open(fileName)
        except IOError:
            commons.respond(
                messageType="ERROR",
                message=f"File {fileName} exists but is not an image. Only jpg and png files are valid",
                code=7
            )
    else:
        commons.respond(
            messageType="ERROR",
            message=f"No such file {fileName}",
            code=8
        )

    # If S3 name was not specified, use fileName
    if s3Name is None:
        objectName = commons.parseObjectName(fileName)
    else:
        objectName = commons.parseImageObject(s3Name)

    # For gestures include the locktype folder path
    if locktype is not None:
        objectName = f"users/{username}/{locktype}/{objectName}"
    else:
        objectName = f"users/{username}/{objectName}"

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

def constructGestureFramework(imagePaths, username, locktype):
    """constructGestureFramework() : Uploads gesture recognition images to the user's S3 folder
    :param imagePaths: List of images paths (in combination order) to upload
    :param username: Username folder to upload the images to
    :param locktype: Either lock or unlock (usually), depicts which combination the images are a part of
    :returns: A completed gestures.json config file
    """
    position = 1
    gestureConfig = {}
    for path in imagePaths:
        s3ObjectPath = upload_file(path, username, locktype)
        commons.respond(messageType="SUCCESS", message=f"Gesture locking image ({path}) has been successfully uploaded for position {position}", code=0)
        gestureConfig[str(position)] = { "path" : s3ObjectPath }
        position += 1
    return gestureConfig

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
    argumentParser.add_argument("-f", "--face",
        required=False,
        help="Path to the jpg or png image file to use as your facial recognition face to compare against when streaming"
    )
    argumentParser.add_argument("-l", "--lock-gestures",
        required=False,
        action="extend",
        help="Paths to jpg or png image files (seperated with spaces) to use as your lock gesture recognition combination when streaming"
    )
    argumentParser.add_argument("-u", "--unlock-gestures",
        required=False,
        action="extend",
        help="Paths to jpg or png image files (seperated with spaces) to use as your unlock gesture recognition combination when streaming"
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
    argumentParser.add_argument("-p", "--profile",
        required=False,
        help="Username to retrieve the gestures from AWS for comparison with the gestures performed on the stream\nUsed with -a gesture"
    )
    argDict = argumentParser.parse_args()
    print("[INFO] Parsed arguments:")
    print(argDict)

    # Add a new user face
    # TODO: Add the ability to add a gesture combination here too
    if argDict.action == "create":
        # Verify we have a lock and unlock gesture
        if argDict.lock is [] and argDict.unlock is []:
            commons.respond(
                messageType="ERROR",
                message=f"-l or -u was not given. Please provide a locking and unlocking gesture so your user account can be created.",
                code=13
            )
        # Verify we have a username to upload the object to
        if argDict.profile is None:
            commons.respond(
                messageType="ERROR",
                message=f"-p was not given. Please provide a profile username for your account.",
                code=13
            )

        uploadedImage = upload_file(argDict.face, argDict.profile, None, argDict.name)

        # Immediately index the photo into a local collection if param is set
        if argDict.index == True:
            print(f"[INFO] Indexing photo into {commons.FACE_RECOG_COLLECTION}")
            # uploadedImage will the objectName so no need to check if there is a user in this function
            indexedImage = index_photo.add_face_to_collection(uploadedImage)
            commons.respond(
                messageType="SUCCESS",
                message=f"{uploadedImage} successfully uploaded to S3 and indexed into the Rekognition Collection.",
                content=indexedImage,
                code=0
            )
        else:
            commons.respond(
                messageType="SUCCESS",
                message=f"{uploadedImage} was successfully uploaded to S3 (not indexed). Specify -i to index into the Rekognition client.",
                code=0
            )

        # Iterate over the lock and unlock image files, uploading them one a time while constructing our gestures.json
        lockGestureConfig = constructGestureFramework(argDict.lock, argDict.profile, "lock")
        unlockGestureConfig = constructGestureFramework(argDict.unlock, argDict.profile, "unlock")
        gestureConfig = { "lock" : lockGestureConfig, "unlock" : unlockGestureConfig }

        # Finally, upload our completed gestures.json
        print("[INFO] Images have been successfully uploaded. Uploading config file...")
        try:
            client.putObject(
                Body=gestureConfig,
                Bucket=commons.FACE_RECOG_BUCKET,
                Key=f"users/{argDict.profile}/gestureConfig.json"
            )
        except Exception as e:
            commons.respond(
                messageType="ERROR",
                message=f"Failed to upload the gesture configuration file",
                content={ "ERROR" : e },
                code=3
            )

        print("[SUCCESS] Config file uploaded!")
        return commons.respond(
            messageType="SUCCESS",
            message=f"Facial recognition and gesture recognition images and configs files have been successfully uploaded!",
            code=0
        )

    # Ensure the file to be edited or deleted exists. Then, delete it from both the collection and S3 (if needs be)
    elif argDict.action == "delete":

        # Immediately delete the photo from local collection if param is set
        if argDict.index == True:
            print(f"[INFO] Removing photo from {commons.FACE_RECOG_COLLECTION}")
            deletedFace = index_photo.remove_face_from_collection(argDict.face)

        # Verify we have a username to delete the image from
        if argDict.username is None or "":
            commons.respond(
                messageType="ERROR",
                message=f"No username was given to delete an image from. Specify a username with -u/--username",
                code=13
            )

        s3FilePath = f"users/{argDict.username}/{argDict.file}"

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
                    matchedGestures = gesture_recog.checkForGestures(frame, argDict.profile)
                else:
                    commons.respond(
                        messageType="ERROR",
                        message="Stream Interrupted or corrupted!",
                        code=12
                    )
                    break

            # By this point, we have found a set of matching gestures so cancel timeout and return access granted
            signal.alarm(0)
            print(f"[SUCCESS] Matched gesture combination for user {argDict.profile}!")

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
