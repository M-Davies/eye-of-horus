# -----------------------------------------------------------
# Main management file that is the main input source for users and website
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under GNU GPL v3 License
# -----------------------------------------------------------

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from boto3.s3.transfer import TransferConfig
from ratelimit import RateLimitException

import sys
import argparse
import os
import time
import subprocess
import signal
import json
import random
import logging
from PIL import Image
from dotenv import load_dotenv

from face import index_photo
from face import compare_faces
from gesture import gesture_recog
import commons

# GLOBALS
s3Client = boto3.client('s3')
rekogClient = boto3.client('rekognition')
logger = logging.getLogger()
TIMEOUT_SECONDS = 20
load_dotenv()


def delete_file(fileName):
    """delete_file() : Deletes a S3 object file
    :param fileName: S3 Path to file to be deleted
    :return: S3 file object path that was successfully deleted
    """

    try:
        print("[INFO] Deleting...")
        s3Client.delete_object(
            Bucket=os.getenv("FACE_RECOG_BUCKET"),
            Key=fileName
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
            Bucket=os.getenv("FACE_RECOG_BUCKET"),
            Key=fileName
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
            s3Client.upload_fileobj(
                Fileobj=fileBytes,
                Bucket=os.getenv("FACE_RECOG_BUCKET"),
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
            content={"ERROR": str(e)},
            code=3
        )
    except EndpointConnectionError as e:
        return commons.respond(
            messageType="ERROR",
            message=f"{fileName} FAILED to upload to S3. Could not establish a connection to AWS. {errorSuffix}",
            content={"ERROR": str(e)},
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
                message="Stream failed to start (see content for exit code), see log for details",
                content={"ERROR": str(startStreamRet)},
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
                message="Stream failed to die (see CONTENT field is the exit code), see log for details",
                content={"ERROR": str(stopStreamRet)},
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
            Bucket=os.getenv("FACE_RECOG_BUCKET"),
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
        newGestureConfig = {"lock": newGestureLockTypeConfig, "unlock": oldFullConfig["unlock"]}
    else:
        newGestureConfig = {"lock": oldFullConfig["lock"], "unlock": newGestureLockTypeConfig}

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
            Bucket=os.getenv("FACE_RECOG_BUCKET"),
            Key=f"users/{username}/gestures/GestureConfig.json"
        )
    except Exception as e:
        return commons.respond(
            messageType="ERROR",
            message="Failed to upload updated gesture configuration file",
            content={"ERROR": str(e)},
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
        if os.path.isfile(path):
            # Verify local file is an actual image
            try:
                Image.open(path)
            except IOError:
                return commons.respond(
                    messageType="ERROR",
                    message=f"File {path} exists but is not an image. Only jpg and png files are valid",
                    code=7
                )

            # Identify the gesture type
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
                    message="No recognised gesture was found within the image",
                    code=17
                )
        else:
            gestureType = path
            print(f"[WARNING] No image to upload ({gestureType} is the assumed name of the gesture type). Verifying this is a supported gesture type...")
            # We don't need to do this for a file as it is scanned for valid gestures during analysis
            gestureTypes = gesture_recog.getGestureTypes()
            if gestureType not in gestureTypes:
                return commons.respond(
                    messageType="ERROR",
                    message=f"{gestureType} is not an existing file or valid gesture type. Valid gesture types = {gestureTypes}",
                    code=17
                )
            else:
                print(f"[SUCCESS] Gesture type identified as {gestureType}")

        # We leave path empty for now as it's updated when we uploaded the files
        gestureConfig[str(position)] = {"gesture": gestureType, "path": path}
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
                message="The two gesture combinations are identical. Please ensure the combinations are different and not reversed versions of each other",
                code=21
            )

        # One combination is the same as the other when reversed
        if list(previousGestures.copy())[::-1] == userGestures or list(userGestures.copy())[::-1] == previousGestures:
            return commons.respond(
                messageType="ERROR",
                message="One gesture combination is the same as the other when reversed. Please ensure the combinations are different and not reversed versions of each other",
                code=22
            )

    print(f"[SUCCESS] {locktype.capitalize()}ing combination passed all rule restraints!")
    return gestureConfig


def parseArgs(args):
    """parseArgs() : Takes in a specific array or sys args as input and returns a well formatted argument dictionary
    :param args: Array of sys.argv to parse
    :return: A dictionary of args by name
    """
    global TIMEOUT_SECONDS
    argumentParser = argparse.ArgumentParser(
        description="Welcome to the eye of horus facial and gesture recognition authentication system! Please see the command options below for the usage of this tool outside of a website environment.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    argumentParser.add_argument(
        "-a", "--action",
        required=True,
        choices=["create", "edit", "delete", "compare", "gesture"],
        help="""Only one action can be performed at one time:\n\ncreate: Creates a new user --profile in s3 and uploads and indexes the --face file alongside the ----lock-gestures and --unlock-gestures image files. --name can optionally be added if the name of the --face file is not what it should be in S3.\n\nedit: Edits a user --profile account's --face, --lock or --unlock feature. Note: It is not possible to rename a user --profile. Please delete your account and create a new one if you wish to do so.\n\ndelete: Deletes a user --profile account inside S3 by doing the reverse of --action create.\n\ncompare: Starts streaming and executes the facial comparison library against ALL users in the database. You can alter the length of the stream search timeout with --timeout. Alternatively, you can specify a --face to compare against a --user's.\n\ngesture: Takes a number of --lock OR --unlock images as input for authenticating with the gesture recognition client against the user --profile.
        """
    )
    argumentParser.add_argument(
        "-f", "--face",
        required=False,
        help="Path to the jpg or png image file to use as your facial recognition face to compare against when running the kinesis stream"
    )
    argumentParser.add_argument(
        "-l", "--lock",
        required=False,
        action="extend",
        nargs="+",
        help="ABSOLUTE Paths to jpg or png image files (seperated with spaces) to use as the --profile user's lock gesture recognition combination. Use with -a edit/create to construct a new combination OR with -a gesture to attempt to authenticate with the matching gestures"
    )
    argumentParser.add_argument(
        "-u", "--unlock",
        required=False,
        action="extend",
        nargs="+",
        help="ABSOLUTE Paths to jpg or png image files (seperated with spaces) to use as the --profile user's unlock gesture recognition combination. Use with -a edit/create to construct a new combination OR with -a gesture to attempt to authenticate with the matching gestures"
    )
    argumentParser.add_argument(
        "-n", "--name",
        required=False,
        help="S3 name of the face image to be uploaded. This is what the image will be stored as in S3. If not specified, the filename passed to --file is used instead."
    )
    argumentParser.add_argument(
        "-t", "--timeout",
        required=False,
        type=int,
        help=f"Timeout (in seconds) for the stream to timeout after not finding a face during comparison\nUsed with -a compare, default is {TIMEOUT_SECONDS}"
    )
    argumentParser.add_argument(
        "-p", "--profile",
        required=False,
        help="Username to perform the -a action upon. Result depends on the action chosen"
    )
    argumentParser.add_argument(
        "-m", "--maintain",
        action="store_true",
        required=False,
        help="If this parameter is set, the gesture recognition project will not be shutdown after rekognition is complete (only applicable with -a create,gesture,edit)"
    )
    argDict = argumentParser.parse_args(args)
    print("[INFO] Parsed arguments:")
    print(f"{argDict}\n")
    return argDict


#########
# START #
#########
def main(parsedArgs=None):
    """main() : Main method that parses the input opts and returns the result"""
    global TIMEOUT_SECONDS
    # Delete old response file if it exists
    if os.path.isfile(os.getenv("RESPONSE_FILE_PATH")):
        try:
            os.remove(os.getenv("RESPONSE_FILE_PATH"))
        except Exception as e:
            print(f"[WARNING] Failed to delete old response json file\n{e}")

    # Parse input parameters
    if parsedArgs is None:
        # Parse with sys args if running by command line
        argDict = parseArgs(sys.argv[1:])
    else:
        # Assume the args have already been parsed
        argDict = parsedArgs

    # Create a new user profile in the rekognition collection and s3
    if argDict.action == "create":
        # Verify we have a face to create
        if argDict.face is None:
            return commons.respond(
                messageType="ERROR",
                message="-f was not given. Please provide a face to be used in recognition for your account.",
                code=13
            )
        else:
            if os.path.isfile(argDict.face):
                try:
                    Image.open(argDict.face)
                except IOError:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"File {argDict.face} exists but is not an image. Only jpg and png files are valid",
                        code=7
                    )
            else:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Could not find file {argDict.face}",
                    code=8
                )
        # Verify we have a lock and unlock gesture combination
        if argDict.lock is None or argDict.unlock is None:
            return commons.respond(
                messageType="ERROR",
                message="-l or -u was not given. Please provide locking (-l) and unlocking (-u) gesture combinations so your user account can be created.",
                code=13
            )
        # Verify we have a username to upload the object to
        if argDict.profile is None:
            return commons.respond(
                messageType="ERROR",
                message="-p was not given. Please provide a profile username for your account.",
                code=13
            )

        # uploadedImage will the objectName so no need to check if there is a user in this function
        index_photo.add_face_to_collection(argDict.face)

        # First, start the rekog project so we can actually analyse the given images
        gesture_recog.projectHandler(True)

        try:
            # Now iterate over lock and unlock image files, processing one a time while constructing our gestures.json
            lockGestureConfig = constructGestureFramework(argDict.lock, argDict.profile, "lock")
            unlockGestureConfig = constructGestureFramework(argDict.unlock, argDict.profile, "unlock", lockGestureConfig)
            gestureConfig = {"lock": lockGestureConfig, "unlock": unlockGestureConfig}
        finally:
            # Finally, close down the rekog project if specified
            if argDict.maintain is False:
                gesture_recog.projectHandler(False)

        # Finally, upload all the files featured in these processes (including the gesture config file)
        print("[INFO] All tests passed and profiles constructing. Uploading face...")

        # Upload face
        try:
            if argDict.name is not None:
                upload_file(argDict.face, argDict.profile, None, argDict.name)
            else:
                upload_file(argDict.face, argDict.profile, None, f"{argDict.profile}.jpg")
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
                Bucket=os.getenv("FACE_RECOG_BUCKET"),
                Key=f"users/{argDict.profile}/gestures/GestureConfig.json"
            )
        except Exception as e:
            return commons.respond(
                messageType="ERROR",
                message="Failed to upload the gesture configuration file. Gesture and face images have already been uploaded. Recommend you delete your user account with -a delete and try remaking it.",
                content={"ERROR": str(e)},
                code=3
            )

        print("[SUCCESS] Config file uploaded!")
        return commons.respond(
            messageType="SUCCESS",
            message="Facial recognition and gesture recognition images and configs files have been successfully uploaded!",
            code=0
        )

    elif argDict.action == "edit":
        # Verify we have a user to edit
        if argDict.profile is None:
            return commons.respond(
                messageType="ERROR",
                message="-p was not given. Please provide a profile username for your account.",
                code=13
            )
        else:
            try:
                s3Client.get_object_acl(
                    Bucket=os.getenv("FACE_RECOG_BUCKET"),
                    Key=f"users/{argDict.profile}/{argDict.profile}.jpg"
                )
            except s3Client.exceptions.NoSuchKey:
                return commons.respond(
                    messageType="ERROR",
                    message=f"User {argDict.profile} does not exist or failed to face file",
                    code=9
                )
        if argDict.face is None and argDict.lock is None and argDict.unlock is None:
            # Verify at least one editable feature was given
            return commons.respond(
                messageType="ERROR",
                message="Neither -f, -u or -l was given. Please provide a profile feature to edit.",
                code=13
            )

        if argDict.face is not None:
            # Check that face file exists now as it will try to delete from collection without verify otherwise
            if os.path.isfile(argDict.face):
                try:
                    Image.open(argDict.face)
                except IOError:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"File {argDict.face} exists but is not an image. Only jpg and png files are valid",
                        code=7
                    )
            else:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Could not find file {argDict.face}",
                    code=8
                )

            # Delete old user image from collection
            print(f"[INFO] Removing old face from {os.getenv('FACE_RECOG_COLLECTION')} for user {argDict.profile}")
            deletedFace = index_photo.remove_face_from_collection(f"{argDict.profile}.jpg")
            if deletedFace is None:
                # This can sometimes happen if deletion was attempted before but was not completed
                print(f"[WARNING] No face found in {os.getenv('FACE_RECOG_COLLECTION')} for user {argDict.profile}. We will assume it has already been removed.")
            index_photo.add_face_to_collection(argDict.face)

            # Replace user face in S3
            try:
                upload_file(argDict.face, argDict.profile, None, f"{argDict.profile}.jpg")
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

                if argDict.lock is not None and argDict.unlock is not None:
                    # We are editing both combinations so run rules and construction sequentially
                    adjustedLock = adjustConfigFramework(argDict.lock, argDict.profile, "lock")
                    print(f"[SUCCESS] Lock gesture combination has been successfully replaced for user {argDict.profile}")
                    adjustConfigFramework(argDict.unlock, argDict.profile, "unlock", adjustedLock["lock"])
                    print(f"[SUCCESS] Unlock gesture combination has been successfully replaced for user {argDict.profile}")
                else:
                    # Get user config to compare edited rules against
                    currentConfig = gesture_recog.getUserCombinationFile(argDict.profile)
                    if argDict.lock is not None:
                        adjustConfigFramework(argDict.lock, argDict.profile, "lock", currentConfig["unlock"])
                        print(f"[SUCCESS] Lock gesture combination has been successfully replaced for user {argDict.profile}")
                    else:
                        adjustConfigFramework(argDict.unlock, argDict.profile, "unlock", currentConfig["lock"])
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
                message="-p was not specified. Please pass in a user account name to delete.",
                code=13
            )

        # Remove relevant face from rekog collection
        print(f"[INFO] Removing face from {os.getenv('FACE_RECOG_COLLECTION')} for user {argDict.profile}")
        deletedFace = index_photo.remove_face_from_collection(f"{argDict.profile}.jpg")
        if deletedFace is None:
            # This can sometimes happen if deletion was attempted before but was not completed
            print(f"[WARNING] No face found in {os.getenv('FACE_RECOG_COLLECTION')} for user {argDict.profile}. We will assume it has already been removed.")

        # Check the user's folder actually exists in s3
        print(f"[INFO] Deleting user folder for {argDict.profile} from s3...")
        s3FilePath = f"users/{argDict.profile}/{argDict.profile}.jpg"
        try:
            s3Client.get_object_acl(
                Bucket=os.getenv('FACE_RECOG_BUCKET'),
                Key=s3FilePath
            )
        except s3Client.exceptions.NoSuchKey:
            return commons.respond(
                messageType="ERROR",
                message="No such user profile exists",
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
        if argDict.face is not None:
            # Verify params
            if argDict.profile is None or "":
                return commons.respond(
                    messageType="ERROR",
                    message="-p was not specified. Please pass in a user account name",
                    code=13
                )

            if os.path.isfile(argDict.face):
                try:
                    Image.open(argDict.face)
                except IOError:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"File {argDict.face} exists but is not an image. Only jpg and png files are valid",
                        code=7
                    )
            else:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Could not find file {argDict.face}",
                    code=8
                )

            # Run face comparison
            print(f"[INFO] Running facial comparison library to compare {argDict.face} against the stored face for {argDict.profile}")
            faceCompare = compare_faces.compareFaces(argDict.face, argDict.profile)
            if faceCompare["FaceMatches"] is not [] and len(faceCompare["FaceMatches"]) == 1:
                return commons.respond(
                    messageType="SUCCESS",
                    message=f"Input face {argDict.face} matched successfully with stored user's {argDict.profile} face",
                    code=0
                )
            else:
                return commons.respond(
                    messageType="ERROR",
                    message=f"Input face {argDict.face} does not match stored user's {argDict.profile} face",
                    code=10
                )
        else:
            if argDict.timeout is not None:
                TIMEOUT_SECONDS = argDict.timeout

            print(f"[INFO] Running facial comparison library to check for user faces in current stream (timing out after {TIMEOUT_SECONDS}s)...")

            # Start/end stream
            streamHandler(True, 3)

            # Start comparing, timing out if no face is found within the limit
            try:
                signal.signal(signal.SIGALRM, timeoutHandler)
                signal.alarm(TIMEOUT_SECONDS)
                matchedFace = compare_faces.checkForFaces()

                # By this point, we have found a face so cancel the timeout and return the matched face
                signal.alarm(0)
                return commons.respond(
                    messageType="SUCCESS",
                    message="Found a matching face!",
                    content=matchedFace,
                    code=0
                )
            except TimeoutError:
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                return commons.respond(
                    messageType="ERROR",
                    message=f"TIMEOUT FIRED AFTER {TIMEOUT_SECONDS}s, NO FACES WERE FOUND IN THE STREAM!",
                    code=10
                )
            finally:
                # Reset signal handler everytime
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                streamHandler(False)

    # Run gesture recognition against given images
    elif argDict.action == "gesture":
        if argDict.profile is None:
            return commons.respond(
                messageType="ERROR",
                message="-p was not given. Please pass a user profile to conduct gesture recognition against",
                code=13
            )

        # We can't try to unlock AND lock the system at the same time
        if argDict.lock is not None and argDict.unlock is not None:
            return commons.respond(
                messageType="ERROR",
                message="Cannot lock (-l) and unlock (-u) at the same time.",
                code=13
            )
        # Likewise, we cannot try to find a gesture if we don't know which locktype to authenticate with
        elif argDict.lock is None and argDict.unlock is None:
            return commons.respond(
                messageType="ERROR",
                message="Neither Lock (-l) or Unlock (-u) indicator was given.",
                code=13
            )
        # Otherwise, figure out if we are locking or unlocking
        else:
            if argDict.lock is not None:
                locktype = "lock"
                imagePaths = argDict.lock
            else:
                locktype = "unlock"
                imagePaths = argDict.unlock

        # Start rekognition model
        gesture_recog.projectHandler(True)

        # Get user's combination length to identify when we have filled the combination
        userComboLength = int(max(gesture_recog.getUserCombinationFile(argDict.profile)[locktype]))
        try:
            print(f"[INFO] Running gesture recognition library to check for the correct {locktype}ing gestures performed in the given images...")

            matchedGestures = 1
            for path in imagePaths:
                # Verify file exists
                if os.path.isfile(path):
                    try:
                        Image.open(path)
                    except IOError:
                        return commons.respond(
                            messageType="ERROR",
                            message=f"File {path} exists but is not an image. Only jpg and png files are valid.",
                            code=7
                        )
                else:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"File does not exist at {path}",
                        code=8
                    )

                # Run gesture recog lib
                try:
                    foundGesture = gesture_recog.checkForGestures(path)
                except rekogClient.exceptions.ImageTooLargeException:
                    print(f"[WARNING] {path} is too large (>4MB) to check for gestures directly. Uploading to S3 first and then checking for gestures...")

                    # The s3 filename is going to be temporarily added and then deleted
                    s3FilePath = f"temp/image_{str(random.randrange(1,1000000))}.jpg"
                    try:
                        gestureObjectPath = upload_file(path, argDict.profile, None, s3FilePath)
                    except FileNotFoundError:
                        return commons.respond(
                            messageType="ERROR",
                            message=f"Could not find file at {path}",
                            code=8
                        )
                    delete_file(s3FilePath)
                    foundGesture = gesture_recog.checkForGestures(gestureObjectPath)

                if foundGesture is not None:
                    print(f"[INFO] Checking if the {locktype} combination contains the same gesture at position {matchedGestures}...")
                    try:
                        hasGesture = gesture_recog.inUserCombination(foundGesture, argDict.profile, locktype, str(matchedGestures))
                    except RateLimitException:
                        return commons.respond(
                            messageType="ERROR",
                            message="Too many user requests in too short a time. Please try again later",
                            code=26
                        )

                    # User has same gesture and in right position, don't dump log as malicious users could figure out which gestures are correct
                    if hasGesture is True:
                        matchedGestures += 1
                        continue
                else:
                    return commons.respond(
                        messageType="ERROR",
                        message=f"No gesture was found in image {path}",
                        code=17
                    )

            if matchedGestures - 1 == userComboLength:
                return commons.respond(
                    messageType="SUCCESS",
                    message=f"Matched {locktype} gesture combination for user {argDict.profile}",
                    code=0
                )
            else:
                # Include this check just in case something goes wrong with the timeout handler
                return commons.respond(
                    messageType="ERROR",
                    message="Incorrect gesture combination was given",
                    code=18
                )

        finally:
            if argDict.maintain is False:
                gesture_recog.projectHandler(False)

    else:
        return commons.respond(
            messageType="ERROR",
            message=f"Invalid action type - {argDict.action}",
            code=13
        )


if __name__ == "__main__":
    main()
