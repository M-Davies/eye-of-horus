# -----------------------------------------------------------
# Uploads an image containing a face to S3
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# -----------------------------------------------------------

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from boto3.s3.transfer import TransferConfig

import cv2
import sys
import argparse
import os
import time
import subprocess
import signal
import json
from datetime import datetime
from PIL import Image

from face import index_photo
from face import compare_faces
from gesture import gesture_recog
import commons

# GLOBALS
s3Client = boto3.client('s3')
rekogClient = boto3.client('rekognition')

def delete_file(fileName):
    """delete_file() : Deletes a S3 object file
    :param fileName: S3 Path to file to be deleted
    :return: S3 file object path that was successfully deleted
    """

    try:
        print("[INFO] Deleting...")
        s3Client.delete_object(
            Bucket = commons.FACE_RECOG_BUCKET,
            Key = fileName
        )
    except EndpointConnectionError:
        return commons.respond(
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
        return commons.respond(
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
    # This is appended to an error messsage in case the user is creating an account and something goes wrong
    errorSuffix = "WARNING: If you are executing this via manager.py -a create your profile has been partially created on s3. To ensure you do not suffer hard to debug problems, please ensure you delete your profile with -a delete before trying -a create again"

    # Verify file exists
    if os.path.isfile(fileName):
        try:
            Image.open(fileName)
        except IOError:
            return commons.respond(
                messageType="ERROR",
                message=f"File {fileName} exists but is not an image. Only jpg and png files are valid. {errorSuffix}",
                code=7
            )
    else:
        # Throw an error here instead of a response as sometimes the file will be a label for gesture recognition
        raise FileNotFoundError

    # If S3 name was not specified, use fileName
    if s3Name is None:
        objectName = commons.parseObjectName(fileName)
    else:
        objectName = commons.parseImageObject(s3Name)

    # For gestures include the locktype folder path
    if locktype is not None:
        objectName = f"users/{username}/gestures/{locktype}/{objectName}"
    else:
        objectName = f"users/{username}/{objectName}"

    # Upload the file
    try:
        print(f"[INFO] Uploading {fileName}...")
        # Sometimes this will time out on a first file upload
        with open(fileName, "rb") as fileBytes:
            response = s3Client.upload_fileobj(
                Fileobj=fileBytes,
                Bucket=commons.FACE_RECOG_BUCKET,
                Key=objectName,
                Config=TransferConfig(
                    multipart_threshold=16777216,
                    max_concurrency=20,
                    num_download_attempts=10
                )
            )
    except ClientError as e:
        return commons.respond(
            messageType="ERROR",
            message=f"{fileName} FAILED to upload to S3. {errorSuffix}",
            content={ "ERROR" : str(e) },
            code=3
        )
    except EndpointConnectionError as e:
        return commons.respond(
            messageType="ERROR",
            message=f"{fileName} FAILED to upload to S3. Could not establish a connection to AWS. {errorSuffix}",
            content={ "ERROR" : str(e) },
            code=3
        )

    return objectName

def streamHandler(start, sleepTime=None):
    """streamHandler() : Starts or stops the live stream to AWS, sleeping after starting briefly to allow it to get situated. It will also check the error codes of the respective start and stop shell scripts to verify the stream actually started/stopped.
    :param start: Boolean denoting whether we are starting or stopping the stream
    :param sleepTime: Int for how long to sleep for after starting the stream
    """
    if start:
        # Boot up live stream
        startStreamRet = subprocess.call("./startStream.sh", close_fds=True)
        if startStreamRet != 0:
            return commons.respond(
                messageType="ERROR",
                message=f"Stream failed to start (see content for exit code), see log for details",
                content={ "ERROR" : str(startStreamRet) },
                code=5
            )
        else:
            # We have to sleep for a bit here as the steam takes time to boot, then return control to caller
            time.sleep(sleepTime)
    else:
        # Terminate streaming and reset signal handler everytime
        stopStreamRet = subprocess.call("./stopStream.sh")

        if stopStreamRet != 0:
            return commons.respond(
                messageType="ERROR",
                message=f"Stream failed to die (see CONTENT field is the exit code), see log for details",
                content={ "ERROR" : str(stopStreamRet) },
                code=6
            )

def timeoutHandler(signum, stackFrame):
    """timeoutHandler() : Raises a TimeoutError when the signal alarm goes off. We have to pass in the unused signnum and stackFrame otherwise the signal handler will not fire correctly
    :param signum: Signal handler caller number
    :param stackFrame: Current stack frame object where it was aborted
    """
    raise TimeoutError

def adjustConfigFramework(imagePaths, username, locktype, previousFramework=None):
    """adjustConfigFramework() : Modifies a gesture configuration file according to the user's edit changes
    :param imagePaths: New gesture paths to add
    :param username: User's config file to update
    :param locktype: Lock or unlock combination to update
    :param previousFramework: If a lock gesture has been generated, use it to run the tests in the downstream construction
    :return: Updated config dictionary
    """
    # Retrieve old configuration file
    try:
        oldFullConfig = json.loads(s3Client.get_object(
            Bucket=commons.FACE_RECOG_BUCKET,
            Key=f"users/{username}/gestures/GestureConfig.json"
        )["Body"].read())
    except s3Client.exceptions.NoSuchKey:
        return commons.respond(
            messageType="ERROR",
            message=f"{username} is not an existing user or download of the user details failed",
            code=2
        )

    # Adjust file to account for changes
    newGestureLockTypeConfig = constructGestureFramework(imagePaths, username, locktype, previousFramework)
    if locktype == "lock":
        newGestureConfig = { "lock" : newGestureLockTypeConfig, "unlock" : oldFullConfig["unlock"] }
    else:
        newGestureConfig = { "lock" : oldFullConfig["lock"], "unlock" : newGestureLockTypeConfig }

    # Upload new gestures, adjusting the path of the config file to be s3 relative
    for position, details in newGestureConfig[locktype].items():
        try:
            gestureObjectPath = upload_file(details["path"], username, locktype, f"{locktype.capitalize()}Gesture{position}")
        except FileNotFoundError:
            return commons.respond(
                messageType="ERROR",
                message=f"Could no longer find file {details['path']}",
                code=8
            )
        newGestureConfig[locktype][position]["path"] = gestureObjectPath

    # Upload gesture configuration file
    try:
        s3Client.put_object(
            Body=json.dumps(newGestureConfig, indent=2).encode("utf-8"),
            Bucket=commons.FACE_RECOG_BUCKET,
            Key=f"users/{username}/gestures/GestureConfig.json"
        )
    except Exception as e:
        return commons.respond(
            messageType="ERROR",
            message=f"Failed to upload updated gesture configuration file",
            content={ "ERROR" : str(e) },
            code=3
        )

    return newGestureConfig

def constructGestureFramework(imagePaths, username, locktype, previousFramework=None):
    """constructGestureFramework() : Uploads gesture recognition images and config file to the user's S3 folder
    :param imagePaths: List of images paths or gesture types (in combination order)
    :param username: Username as per their s3 folder
    :param locktype: Either lock or unlock (usually), depicts which combination the images are a part of
    :param previousFramework: If a framework has already been created, we will run tests against both it and the soon to be created framework in tandem
    :returns: A completed gestures.json config
    """
    position = 1
    gestureConfig = {}
    for path in imagePaths:
        try:
            print(f"[INFO] Identifying gesture type for {path}")
            try:
                gestureType = gesture_recog.checkForGestures(path)
            except rekogClient.exceptions.ImageTooLargeException:
                print(f"[WARNING] {path} is too large (>4MB) to check for gestures directly. Uploading to S3 first and then checking for gestures.")
                try:
                    gestureObjectPath = upload_file(path, username, locktype, f"{locktype.capitalize()}Gesture{position}")
                except FileNotFoundError:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"Could no longer find file {path}",
                        code=8
                    )
                gestureType = gesture_recog.checkForGestures(gestureObjectPath)

            if gestureType is not None:
                # Extract the actual gesture type here since error's will return None above
                gestureType = gestureType['Name']
                print(f"[SUCCESS] Gesture type identified as {gestureType}")
            else:
                return commons.respond(
                    messageType="ERROR",
                    message=f"No recognised gesture was found within the image",
                    code=17
                )
        except FileNotFoundError:
            gestureType = path
            print(f"[WARNING] No image to upload ({gestureType} is the assumed name of the gesture type). Verifying this is a supported gesture type...")
            # We don't need to do this for a file as it is scanned for valid gestures during analysis
            gestureTypes = gesture_recog.getGestureTypes()
            if gestureType not in gestureTypes:
                return commons.respond(
                    messageType="ERROR",
                    message=f"{gestureType} is not a valid gesture type. Valid gesture types = {gestureTypes.join(' ')}",
                    code=17
                )
            else:
                print(f"[SUCCESS] Gesture type identified as {gestureType}")

        # We leave path empty for now as it's updated when we uploaded the files
        gestureConfig[str(position)] = { "gesture" : gestureType, "path" : path }
        position += 1

    # Finally, verify we are not using bad "password" practices (e.g. all the same values)
    print("[INFO] Checking combination meets rule requirements...")
    userGestures = list(map(
        lambda position: gestureConfig[position]["gesture"],
        gestureConfig
    ))

    # All gestures are the same in one combination
    if len(set(userGestures)) == 1:
        return commons.respond(
            messageType="ERROR",
            message=f"All gestures for {locktype}ing combination are the same. Please specify at least one different gesture in your combination",
            code=20
        )

    # Conduct tests against the previous gesture combination that was created
    if previousFramework is not None:
        previousGestures = list(map(
            lambda position: previousFramework[position]["gesture"],
            previousFramework
        ))

        # Both combinations are the same
        if previousGestures == userGestures:
            return commons.respond(
                messageType="ERROR",
                message=f"The two gesture combinations are identical. Please ensure the combinations are different and not reversed versions of each other",
                code=21
            )

        # One combination is the same as the other when reversed
        if list(previousGestures.copy())[::-1] == userGestures or list(userGestures.copy())[::-1] == previousGestures:
            return commons.respond(
                messageType="ERROR",
                message=f"One gesture combination is the same as the other when reversed. Please ensure the combinations are different and not reversed versions of each other",
                code=22
            )

    print(f"[SUCCESS] {locktype.capitalize()}ing combination passed all rule restraints!")
    return gestureConfig

#########
# START #
#########
def main(argv):
    """main() : Main method that parses the input opts and returns the result"""

    # Parse input parameters
    argumentParser = argparse.ArgumentParser(
        description="Welcome to the eye of horus facial and gesture recognition authentication system! Please see the command options below for the usage of this tool outside of a website environment.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    argumentParser.add_argument("-a", "--action",
        required=True,
        choices=["create", "edit", "delete", "compare", "gesture"],
        help="""Only one action can be performed at one time:\n\ncreate: Creates a new user --profile in s3 and uploads and indexes the --face file alongside the ----lock-gestures and --unlock-gestures image files. --name can optionally be added if the name of the --face file is not what it should be in S3.\n\edit: Edits a user --profile account's --face, --lock or --unlock feature. Note: It is not possible to rename a user --profile. Please delete your account and create a new one if you wish to do so.\n\ndelete: Deletes a user --profile account inside S3 by doing the reverse of --action create.\n\ncompare: Starts streaming and executes the facial comparison library against ALL users in the database. You can alter the length of the stream search timeout with --timeout\n\ngesture: Starts streaming and executes the gesture comparison library against the user --profile.
        """
    )
    argumentParser.add_argument("-f", "--face",
        required=False,
        help="Path to the jpg or png image file to use as your facial recognition face to compare against when running the kinesis stream"
    )
    argumentParser.add_argument("-l", "--lock",
        required=False,
        action="extend",
        nargs="+",
        help="Two options for this command:\n1) FOR -a create OR -a edit = ABSOLUTE Paths to jpg or png image files (seperated with spaces) to use as the --profile user's lock gesture recognition combination when streaming\n2) FOR -a gesture = Simply specify this param with -l YES to declare that the user --profile wishes to attempt to lock their system using their lock gesture pattern"
    )
    argumentParser.add_argument("-u", "--unlock",
        required=False,
        action="extend",
        nargs="+",
        help="Two options for this command:\n1)FOR -a create OR -a edit = ABSOLUTE Paths to jpg or png image files (seperated with spaces) to use as the --profile user's unlock gesture recognition combination when streaming\n2) FOR -a gesture = Simply specify this param with -u YES to declare that the user --profile wishes to attempt to unlock their system using their unlock gesture pattern"
    )
    argumentParser.add_argument("-n", "--name",
        required=False,
        help="S3 name of the face image to be uploaded. This is what the image will be stored as in S3. If not specified, the filename passed to --file is used instead."
    )
    timeoutSecondsFace = 20
    timeoutSecondsGesture = 60
    argumentParser.add_argument("-t", "--timeout",
        required=False,
        type=int,
        help=f"Timeout (in seconds) for the stream to timeout after not finding a face or gesture during comparison\nUsed with -a compare or -a gesture, default is {timeoutSecondsFace} for facial recognition, {timeoutSecondsGesture} for gesture recognition"
    )
    argumentParser.add_argument("-p", "--profile",
        required=False,
        help="Username to perform -a create,delete,compare action upon. Result depends on the action chosen"
    )
    argumentParser.add_argument("-m", "--maintain",
        action="store_true",
        required=False,
        help="If this parameter is set, the gesture recognition project will not be closed after rekognition is complete (only applicable with -a create,gesture,edit)"
    )
    argDict = argumentParser.parse_args()
    print("[INFO] Parsed arguments:")
    print(f"{argDict}\n")

    # Create a new user profile in the rekognition collection and s3
    if argDict.action == "create":
        # Verify we have a face to create
        if argDict.face is None:
            return commons.respond(
                messageType="ERROR",
                message=f"-f was not given. Please provide a face to be used in recognition for your account.",
                code=13
            )
        # Verify we have a lock and unlock gesture combination
        if argDict.lock is None and argDict.unlock is None:
            return commons.respond(
                messageType="ERROR",
                message=f"-l or -u was not given. Please provide locking (-l) and unlocking (-u) gesture combinations so your user account can be created.",
                code=13
            )
        # Verify the gesture combinations are at least 4 gestures in length
        if len(argDict.lock) < 4 or len(argDict.unlock) < 4:
            return commons.respond(
                messageType="ERROR",
                message=f"Each gesture combination must be at least 4 gestures in length",
                code=13
            )
        # Verify we have a username to upload the object to
        if argDict.profile is None:
            return commons.respond(
                messageType="ERROR",
                message=f"-p was not given. Please provide a profile username for your account.",
                code=13
            )

        # uploadedImage will the objectName so no need to check if there is a user in this function
        indexedImage = index_photo.add_face_to_collection(argDict.face)

        # First, start the rekog project so we can actually analyse the given images
        gesture_recog.projectHandler(True)

        try:
            # Now iterate over lock and unlock image files, processing one a time while constructing our gestures.json
            lockGestureConfig = constructGestureFramework(argDict.lock, argDict.profile, "lock")
            unlockGestureConfig = constructGestureFramework(argDict.unlock, argDict.profile, "unlock", lockGestureConfig)
            gestureConfig = { "lock" : lockGestureConfig, "unlock" : unlockGestureConfig }
        finally:
            # Finally, close down the rekog project if specified
            if argDict.maintain is False:
                gesture_recog.projectHandler(False)

        # Finally, upload all the files featured in these processes (including the gesture config file)
        print("[INFO] All tests passed and profiles constructing. Uploading face...")

        # Upload face
        try:
            uploadedImage = upload_file(argDict.face, argDict.profile, None, argDict.name)
        except FileNotFoundError:
            return commons.respond(
                messageType="ERROR",
                message=f"No such file {argDict.face}",
                code=8
            )

        # Upload gestures, adjusting the path of the config file to be s3 relative
        for locktype in gestureConfig.keys():
            for position, details in gestureConfig[locktype].items():
                try:
                    gestureObjectPath = upload_file(details["path"], argDict.profile, locktype, f"{locktype.capitalize()}Gesture{position}")
                except FileNotFoundError:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"Could no longer find file {details['path']}",
                        code=8
                    )
                gestureConfig[locktype][position]["path"] = gestureObjectPath

        try:
            gestureConfigStr = json.dumps(gestureConfig, indent=2).encode("utf-8")
            s3Client.put_object(
                Body=gestureConfigStr,
                Bucket=commons.FACE_RECOG_BUCKET,
                Key=f"users/{argDict.profile}/gestures/GestureConfig.json"
            )
        except Exception as e:
            return commons.respond(
                messageType="ERROR",
                message=f"Failed to upload the gesture configuration file. Gesture and face images have already been uploaded. Recommend you delete your user account with -a delete and try remaking it.",
                content={ "ERROR" : str(e) },
                code=3
            )

        print("[SUCCESS] Config file uploaded!")
        return commons.respond(
            messageType="SUCCESS",
            message=f"Facial recognition and gesture recognition images and configs files have been successfully uploaded!",
            code=0
        )

    elif argDict.action == "edit":
        # Verify we have a user to edit
        if argDict.profile is None:
            return commons.respond(
                messageType="ERROR",
                message=f"-p was not given. Please provide a profile username for your account.",
                code=13
            )
        else:
            try:
                s3Client.get_object_acl(
                    Bucket = commons.FACE_RECOG_BUCKET,
                    Key = f"users/{argDict.profile}/{argDict.profile}.jpg"
                )
            except s3Client.exceptions.NoSuchKey:
                return commons.respond(
                    messageType="ERROR",
                    message=f"User {argDict.profile} does not exist or failed to retrieve configuration file",
                    code=9
                )
        if argDict.face is None and argDict.lock is None and argDict.unlock is None:
            # Verify at least one editable feature was given
            return commons.respond(
                    messageType="ERROR",
                    message=f"Neither -f, -u or -l was given. Please provide a profile feature to edit.",
                    code=13
            )

        if argDict.face is not None:
            # Delete old user image from collection
            print(f"[INFO] Removing old face from {commons.FACE_RECOG_COLLECTION} for user {argDict.profile}")
            deletedFace = index_photo.remove_face_from_collection(f"{argDict.profile}.jpg")
            if deletedFace is None:
                # This can sometimes happen if deletion was attempted before but was not completed
                print(f"[WARNING] No face found in {commons.FACE_RECOG_COLLECTION} for user {argDict.profile}. We will assume it has already been removed.")
            index_photo.add_face_to_collection(argDict.face)

            # Replace user face in S3
            try:
                uploadedImage = upload_file(argDict.face, argDict.profile, None, f"{argDict.profile}.jpg")
            except FileNotFoundError:
                return commons.respond(
                    messageType="ERROR",
                    message=f"No such file {argDict.face}",
                    code=8
                )
            print(f"[SUCCESS] {argDict.face} has successfully replaced user {argDict.profile} face!")

        # Encase within two conditionals to avoid pointless running of gesture project
        if argDict.lock is not None or argDict.unlock is not None:
            try:
                # Start gesture project to allow for gesture recognition
                gesture_recog.projectHandler(True)

                adjustedLock = None
                if argDict.lock is not None:
                    adjustedLock = adjustConfigFramework(argDict.lock, argDict.profile, "lock")
                    print(f"[SUCCESS] Lock gesture combination has been successfully replaced for user {argDict.profile}")

                if argDict.unlock is not None:
                    adjustedUnlock = adjustConfigFramework(argDict.unlock, argDict.profile, "unlock", adjustedLock["lock"])
                    print(f"[SUCCESS] Unlock gesture combination has been successfully replaced for user {argDict.profile}")

            finally:
                if argDict.maintain is False:
                    gesture_recog.projectHandler(False)

        return commons.respond(
            messageType="SUCCESS",
            message="All done!",
            code=0
        )

    # Ensure the user account to be edited or deleted exists. Then, delete the data from both the collection and S3
    elif argDict.action == "delete":

        # Verify we have a username to delete
        if argDict.profile is None or "":
            return commons.respond(
                messageType="ERROR",
                message=f"-p was not specified. Please pass in a user account name to delete.",
                code=13
            )

        # Remove relevant face from rekog collection
        print(f"[INFO] Removing face from {commons.FACE_RECOG_COLLECTION} for user {argDict.profile}")
        deletedFace = index_photo.remove_face_from_collection(f"{argDict.profile}.jpg")
        if deletedFace is None:
            # This can sometimes happen if deletion was attempted before but was not completed
            print(f"[WARNING] No face found in {commons.FACE_RECOG_COLLECTION} for user {argDict.profile}. We will assume it has already been removed.")

        # Check the user's folder actually exists in s3
        print(f"[INFO] Deleting user folder for {argDict.profile} from s3...")
        s3FilePath = f"users/{argDict.profile}/"
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
            message=f"User profile for {argDict.profile} was successfully removed from S3 and respective face reference removed from the Rekognition Collection.",
            content=deletedFace,
            code=0
        )

    # Run face comparison on stream
    elif argDict.action == "compare":
        if argDict.timeout != None:
            timeoutSecondsFace = argDict.timeout

        print(f"[INFO] Running facial comparison library to check for user faces in current stream (timing out after {timeoutSecondsFace}s)...")

        # Start/end stream
        streamHandler(True, 3)

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

    # Run gesture recognition on stream
    elif argDict.action == "gesture":
        if argDict.profile == None:
            return commons.respond(
                messageType="ERROR",
                message="-p was not given. Please pass a user profile to conduct gesture recognition against",
                code=13
            )

        # We can't try to unlock AND lock the system at the same time
        if argDict.lock is not None and argDict.unlock is not None:
            return commons.respond(
                messageType="ERROR",
                message="Cannot lock (-l) and unlock (-u) at the same time. Please specify one option at a time.",
                code=13
            )
        # Likewise, we cannot try to find a gesture if we don't know which type to search
        elif argDict.lock is None and argDict.unlock is None:
            return commons.respond(
                messageType="ERROR",
                message="Neither Lock (-l) or Unlock (-u) flag was given. Please specify one type of gesture combination to attempt authentication with.",
                code=13
            )
        # Otherwise, figure out if we are locking or unlocking
        else:
            if argDict.lock is not None:
                locktype = "lock"
            else:
                locktype = "unlock"

        if argDict.timeout != None:
            timeoutSecondsGesture = argDict.timeout

        # Start rekognition model so it is ready for when we start streaming
        gesture_recog.projectHandler(True)

        # Get user's combination to identify when we have filled the combination and to save api spamming later
        userConfig = gesture_recog.getUserCombinationFile(argDict.profile)
        userComboLength = int(max(userConfig[locktype]))
        try:
            # Start/end stream
            streamHandler(True, 10)

            # Retrieve stream's session url endpoint
            endpoint = boto3.client('kinesisvideo').get_data_endpoint(
                StreamName = commons.CAMERA_STREAM_NAME,
                APIName = "GET_HLS_STREAMING_SESSION_URL"
            )["DataEndpoint"]

            # Grab the HLS Stream URL from the endpoint. Some errors produced do not inherit the default Exception class
            kvmClient = boto3.client("kinesis-video-archived-media", endpoint_url = endpoint)
            try:
                # Get live stream (only works if stream is active)
                streamUrl = kvmClient.get_hls_streaming_session_url(
                    StreamName = commons.CAMERA_STREAM_NAME,
                    PlaybackMode = "LIVE"
                )["HLSStreamingSessionURL"]
            except (Exception, kvmClient.exceptions.ResourceNotFoundException) as e:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Stream URL was not valid or stream wasn't found. Try restarting the stream and trying again",
                    content={ "ERROR" : str(e) },
                    code=11
                )

            # Start checking for a matching gesture combo, timing out if the correct sequence is not found within the limit
            print(f"[INFO] Running gesture recognition library to check for the correct {locktype}ing gestures performed in current stream (timing out after {timeoutSecondsGesture}s)...")
            vcap = cv2.VideoCapture(streamUrl)

            # Start timer
            signal.signal(signal.SIGALRM, timeoutHandler)
            signal.alarm(timeoutSecondsGesture)

            # Better user feedback to start at 1 rather than 0
            matchedGestures = 1
            frameCounter = 0
            while(matchedGestures <= userComboLength):

                # Capture frame-by-frame
                ret, frame = vcap.read()
                cv2.imshow('frame',frame)

                if ret is not False and frame is not None:

                    # Only look at certain frames to avoid race condition
                    if frameCounter % 15 == 0:
                        # Run gesture recog lib against captured frame
                        foundGesture = gesture_recog.checkForGestures(cv2.imencode(".jpg", frame)[1].tostring())
                        # Timestamp for debug reference
                        now = (datetime.now()).strftime("%H:%M:%S")

                        if foundGesture is not None:
                            # FIXME: Remove this
                            print(f"{now} Checking if the {locktype} combination contains the same gesture as frame {frameCounter} at position {matchedGestures}...")
                            hasGesture = gesture_recog.inUserCombination(foundGesture, argDict.profile, locktype, str(matchedGestures), userConfig)

                            # User has gesture and it's at the right position
                            if hasGesture is True:
                                # FIXME: Remove this
                                print(f"[SUCCESS] Correct gesture given for position {matchedGestures}!")
                                matchedGestures += 1
                                continue
                            else:
                                # FIXME: Remove this
                                print(f"{now} Gesture was found but is not correct")
                        else:
                            # FIXME: Remove this
                            print(f"{now} No gesture was found")
                    frameCounter += 1
                else:
                    return commons.respond(
                        messageType="ERROR",
                        message="Stream Interrupted or corrupted!",
                        content={ "EXIT" : 12, "RETURN VALUE" : str(ret) },
                        code=12
                    )

            # By this point, we have found a set of matching gestures so cancel timeout and return access granted
            signal.alarm(0)
            # -1 as we started at 1 rather than 0
            if matchedGestures-1 == userComboLength:
                return commons.respond(
                    messageType="SUCCESS",
                    message=f"Matched {locktype} gesture combination for user {argDict.profile}",
                    code=0
                )
            else:
                # Include this check just in case something goes wrong with the timeout handler
                return commons.respond(
                    messageType="ERROR",
                    message=f"Stream timeout FAILED to execute. The correct gesture combination was not detected",
                    code=19
                )

        except TimeoutError:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            return commons.respond(
                messageType="ERROR",
                message=f"Timeout fired after {timeoutSecondsGesture}s, correct gesture was not found in the stream",
                code=10
            )
        finally:
            # Reset/stop timer everytime
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            streamHandler(False)

            if argDict.maintain is False:
                gesture_recog.projectHandler(False)

            # When everything done, release the capture
            try:
                vcap.release()
                cv2.destroyAllWindows()
            except UnboundLocalError:
                # Sometimes, we fail before opencv starts up. In which case, there's no need to cease capture
                pass

    else:
        return commons.respond(
            messageType="ERROR",
            message=f"Invalid action type - {argDict.action}",
            code=13
        )

if __name__ == "__main__":
    main(sys.argv[1:])
