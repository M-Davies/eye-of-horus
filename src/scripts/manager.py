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

s3Client = boto3.client('s3')
rekogClient = boto3.client('rekognition')

def delete_file(fileName):
    """delete_file() : Deletes a S3 object file
    :param fileName: S3 Path to file to be deleted
    :return: S3 file object path that was successfully deleted
    """

    try:
        s3Client.delete_object(
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
        deletionRequest = s3Client.get_object_acl(
            Bucket = commons.FACE_RECOG_BUCKET,
            Key = fileName
        )
    except s3Client.exceptions.NoSuchKey:
        print(f"[SUCCESS] {fileName} has been successfully deleted from S3!")
        return fileName
    except EndpointConnectionError:
        commons.respond(
            messageType="ERROR",
            message="FAILED to verify if object was successfully deleted from S3. Could not establish a connection to AWS",
            code=2
        )

    return commons.respond(
        messageType="ERROR",
        message=f"FAILED to verify if {fileName} object was successfully deleted from S3",
        content=deletionRequest,
        code=4
    )

def upload_file(fileName, username, locktype=None, s3Name=None):
    """upload_file() : Uploads a file to an S3 bucket based off the input params entered.
    :param fileName: Path to file to be uploaded
    :param username: User to upload the new face details to
    :param s3Name: S3 object name and or path. If not specified then the filename is used
    :return: S3 object path to the uploaded object
    """
    # Verify file exists
    if os.path.isfile(fileName):
        try:
            Image.open(fileName)
        except IOError:
            return commons.respond(
                messageType="ERROR",
                message=f"File {fileName} exists but is not an image. Only jpg and png files are valid",
                code=7
            )
    else:
        return commons.respond(
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
            response = s3Client.upload_fileobj(
                Fileobj = fileBytes,
                Bucket = commons.FACE_RECOG_BUCKET,
                Key = objectName
            )
    except ClientError as e:
        return commons.respond(
            messageType="ERROR",
            message=f"{fileName} FAILED to upload to S3",
            content={ "ERROR" : e },
            code=3
        )
    except EndpointConnectionError:
        return commons.respond(
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
            return commons.respond(
                messageType="ERROR",
                message=f"Stream failed to start (CONTENT field is the exit code), see log for details",
                content={ "ERROR" : startStreamRet },
                code=5
            )
        else:
            # We have to sleep for a bit here as the steam takes ~3s to boot, then return control to caller
            time.sleep(3)
    else:
        # Terminate streaming and reset signal handler everytime
        stopStreamRet = subprocess.call("./stopStream.sh")

        if stopStreamRet != 0:
            return commons.respond(
                messageType="ERROR",
                message=f"Stream failed to die (see CONTENT field is the exit code), see log for details",
                content={ "ERROR" : stopStreamRet },
                code=6
            )

def timeoutHandler(signum, stackFrame):
    """timeoutHandler() : Raises a TimeoutError when the signal alarm goes off. We have to pass in the unused signnum and stackFrame otherwise the signal handler will not fire correctly
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
        s3ObjectPath = upload_file(path, username, locktype, f"{locktype}Gesture{position}")
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
        help="""Action to be conducted on the --file. Only one action can be performed at one time:\n\ncreate: Creates a new user --profile in s3 and uploads and indexes the --face file alongside the ----lock-gestures and --unlock-gestures image files. --name can optionally be added if the name of the --face file is not what it should be in S3.\n\ndelete: Deletes a user --profile account inside S3 by doing the reverse of --action create.\n\ncompare: Starts streaming and executes the facial comparison library against ALL users in the database. You can alter the length of the stream search timeout with --timeout\n\ngesture: Starts streaming and executes the gesture comparison library against the user --profile.\n\nNote: There is no edit/rename action as S3 doesn't offer object renaming or deletion. If you wish to rename an object, delete the original and create a new one.
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
        help="S3 name of the face image to be uploaded. This is what the image will be stored as in S3. If not specified, the filename passed to --file is used instead."
    )
    timeoutSecondsFace = 20
    timeoutSecondsGesture = 40
    argumentParser.add_argument("-t", "--timeout",
        required=False,
        type=int,
        help=f"Timeout (in seconds) for the stream to timeout after not finding a face or gesture during comparison\nUsed with -a compare or -a gesture, default is {timeoutSecondsFace} for facial recognition, {timeoutSecondsGesture} for gesture recognition"
    )
    argumentParser.add_argument("-p", "--profile",
        required=False,
        help="Username to perform -a create,delete,compare action upon. Result depends on the action chosen"
    )
    argDict = argumentParser.parse_args()
    print("[INFO] Parsed arguments:")
    print(argDict)

    # Create a new user profile in the rekognition collection and s3
    if argDict.action == "create":
        # Verify we have a lock and unlock gesture
        if argDict.lock is [] and argDict.unlock is []:
            return commons.respond(
                messageType="ERROR",
                message=f"-l or -u was not given. Please provide locking (-l) and unlocking (-u) gesture combinations so your user account can be created.",
                code=13
            )
        # Verify we have a username to upload the object to
        if argDict.profile is None:
            return commons.respond(
                messageType="ERROR",
                message=f"-p was not given. Please provide a profile username for your account.",
                code=13
            )

        uploadedImage = upload_file(argDict.face, argDict.profile, None, argDict.name)

        print(f"[INFO] Indexing photo into {commons.FACE_RECOG_COLLECTION}")

        # uploadedImage will the objectName so no need to check if there is a user in this function
        indexedImage = index_photo.add_face_to_collection(uploadedImage)
        print(f"[SUCCESS] {uploadedImage} successfully uploaded to S3 and indexed into the Rekognition Collection.")

        # Iterate over the lock and unlock image files, uploading them one a time while constructing our gestures.json
        lockGestureConfig = constructGestureFramework(argDict.lock, argDict.profile, "lock")
        unlockGestureConfig = constructGestureFramework(argDict.unlock, argDict.profile, "unlock")
        gestureConfig = { "lock" : lockGestureConfig, "unlock" : unlockGestureConfig }

        # Finally, upload our completed gestures.json
        print("[INFO] Images have been successfully uploaded. Uploading config file...")
        try:
            s3Client.putObject(
                Body=gestureConfig,
                Bucket=commons.FACE_RECOG_BUCKET,
                Key=f"users/{argDict.profile}/GestureConfig.json"
            )
        except Exception as e:
            return commons.respond(
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

        # Verify we have a username to delete
        if argDict.profile is None or "":
            return commons.respond(
                messageType="ERROR",
                message=f"No username was given to delete an image from. Specify a username with -u/--username",
                code=13
            )

        # Remove relevant face from rekog collection
        print(f"[INFO] Removing face from {commons.FACE_RECOG_COLLECTION} for user {argDict.profile}")
        deletedFace = index_photo.remove_face_from_collection(argDict.profile)

        # Check the user's folder actually exists in s3
        print(f"[INFO] Deleting user folder for {argDict.profile} from s3...")
        s3FilePath = f"users/{argDict.profile}"
        try:
            s3Client.get_object_acl(
                Bucket = commons.FACE_RECOG_BUCKET,
                Key = s3FilePath
            )
        except s3Client.exceptions.NoSuchKey:
            return commons.respond(
                messageType="ERROR",
                message=f"No such user object {s3FilePath} exists in S3.",
                code=9
            )

        # Delete user folder
        delete_file(s3FilePath)

        return commons.respond(
            messageType="SUCCESS",
            message=f"User folder for {argDict.profile} was successfully removed from S3 and the respective photo removed from the Rekognition Collection.",
            content=deletedFace,
            code=0
        )

    # Run comparison on stream
    elif argDict.action == "compare":
        if argDict.timeout != None:
            timeoutSecondsFace = argDict.timeout

        print(f"[INFO] Running facial comparison library to check for user faces in current stream (timing out after {timeoutSecondsFace}s)...")

        # Start/end stream
        streamHandler(True)

        # Start comparing, timing out if no face is found within the limit
        try:
            signal.signal(signal.SIGALRM, timeoutHandler)
            signal.alarm(timeoutSecondsFace)
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
            return commons.respond(
                messageType="ERROR",
                message=f"TIMEOUT FIRED AFTER {timeoutSecondsFace}s, NO FACES WERE FOUND IN THE STREAM!",
                code=10
            )
        finally:
            # Reset signal handler everytime
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            streamHandler(False)

    # Run gesture recognition lib
    elif argDict.action == "gesture":
        if argDict.profile == None:
            return commons.respond(
                messageType="ERROR",
                message="-p was not given. Please pass a user profile to conduct gesture recognition against",
                code=13
            )

        # Set a higher default timeout for gesture recog as it will take longer
        if argDict.timeout != None:
            timeoutSecondsGesture = argDict.timeout
        print(f"[INFO] Running gesture recognition library to check for the correct gestures performed in current stream (timing out after {timeoutSecondsGesture}s)...")

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
            return commons.respond(
                messageType="ERROR",
                messsage=f"Stream URL was not valid or stream wasn't found. Try restarting the stream and trying again",
                code=11
            )

        # Start checking for a matching gesture combo, timing out if the correct sequence is not found within the limit
        vcap = cv2.VideoCapture(streamUrl)
        try:
            # Start timer
            signal.signal(signal.SIGALRM, timeoutHandler)
            signal.alarm(timeoutSecondsGesture)

            matchedGestures = 1
            while(matchedGestures < 5):

                # Capture frame-by-frame
                ret, frame = vcap.read()

                if ret is not False or frame is not None:
                    # Run gesture recog lib against captured frame
                    foundGesture = gesture_recog.checkForGestures(frame, argDict.profile)

                    print(f"[INFO] Checking if {argDict.username} contains the identified gesture at position {matchedGestures}...")
                    hasGesture = gesture_recog.inUserCombination(foundGesture, argDict.username, matchedGestures)

                    # User has gesture and it's at the right position
                    if hasGesture is True:
                        print(f"[SUCCESS] Correct gesture given for position {matchedGestures}! Checking next gesture...")
                        matchedGestures += 1
                        continue
                    else:
                        print(f"[WARNING] Image for position {matchedGestures} was not the right gesture or the wrong position in the user combination. Checking next image...")
                        continue
                else:
                    return commons.respond(
                        messageType="ERROR",
                        message="Stream Interrupted or corrupted!",
                        content={ "EXIT" : 12, "RETURN VALUE" : ret },
                        code=12
                    )

            # By this point, we have found a set of matching gestures so cancel timeout and return access granted
            signal.alarm(0)
            return commons.respond(
                messageType="SUCCESS",
                message=f"Matched gesture combination for user {argDict.profile}",
                code=0
            )

        except TimeoutError:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            return commons.respond(
                messageType="ERROR",
                message=f"TIMEOUT FIRED AFTER {timeoutSecondsGesture}s, NO GESTURES WERE FOUND IN THE STREAM!",
                code=10
            )
        finally:
            # Reset/stop timer everytime
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            streamHandler(False)

            # When everything done, release the capture
            vcap.release()
            cv2.destroyAllWindows()

    else:
        return commons.respond(
            messageType="ERROR",
            message=f"Invalid action type - {argDict.action}",
            code=13
        )

if __name__ == "__main__":
    main(sys.argv[1:])
