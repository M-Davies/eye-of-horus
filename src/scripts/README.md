# Python Library

These scripts can be used with the accompanying website OR on their own. They are structured in a tree branching out from the main [manager](#Manager) file, which is the entry point for most operations against the application. This document, designed for developers looking to use facial or gesture recognition in their applications, details the various operations you can undertake using this library.

Other than the manager, the library consists of facial and gesture recognition modules as well as a [common module](commons.py) that all the scripts utilise to some extent or another. Some of the scripts can be executed separate to the manager entirely (execute `python <script-name>.py -h` to see if it is permitted against the script) but the manager is the main entry point for all operations.

## Manager

The [manager.py](manager.py) is the main file of this library. It takes in a set of CLI arguments and returns the result in a response file, as well as the console log. As such, this library is designed to be run in a terminal window but can also be executed as a [subprocess in another application](https://nodejs.org/api/child_process.html). The script uses [argparse](https://docs.python.org/3/library/argparse.html) to take in input arguments from the command line. To view the updated helper doc similar to the one below, execute `python manager.py -h`

```
usage: manager.py [-h] -a {create,edit,delete,compare,gesture} [-f FACE] [-l LOCK [LOCK ...]] [-u UNLOCK [UNLOCK ...]] [-n NAME]
                  [-t TIMEOUT] [-p PROFILE] [-m]

Welcome to the eye of horus facial and gesture recognition authentication system! Please see the command options below for the usage of this tool outside of a website environment.

optional arguments:
  -h, --help            show this help message and exit
  -a {create,edit,delete,compare,gesture}, --action {create,edit,delete,compare,gesture}
                        Only one action can be performed at one time:

                        create: Creates a new user --profile in s3 and uploads and indexes the --face file alongside the ----lock-gestures (OPTIONAL) and --unlock-gestures image files. --name can optionally be added if the name of the --face file is not what it should be in S3.

                        edit: Edits a user --profile account's --face, --lock or --unlock feature. If you wish to delete your lock combination, specify --lock DELETE in lieu of entering a combination of gesture types to change your combination to. Note: It is not possible to rename a user --profile. Please delete your account and create a new one if you wish to do so.

                        delete: Deletes a user --profile account inside S3 by doing the reverse of --action create.

                        compare: Starts streaming and executes the facial comparison library against ALL users in the database. Alternatively, you can specify a --face to compare against a --profile's. Or you can specify a --profile on it's own to compare the captured face with that profile's stored face. You can alter the length of the stream search timeout with --timeout.

                        gesture: Takes a number of --lock OR --unlock images as input for authenticating with the gesture recognition client against the user --profile.

  -f FACE, --face FACE  Path to the jpg or png image file to use as your facial recognition face to compare against when running the kinesis stream
  -l LOCK [LOCK ...], --lock LOCK [LOCK ...]
                        ABSOLUTE Paths to jpg or png image files (seperated with spaces) to use as the --profile user's lock gesture recognition combination (OPTIONAL). Use with -a edit/create to construct a new combination or to delete an existing one by specifying DELETE in lieu OR with -a gesture to attempt to authenticate with the matching gestures
  -u UNLOCK [UNLOCK ...], --unlock UNLOCK [UNLOCK ...]
                        ABSOLUTE Paths to jpg or png image files (seperated with spaces) to use as the --profile user's unlock gesture recognition combination. Use with -a edit/create to construct a new combination OR with -a gesture to attempt to authenticate with the matching gestures
  -n NAME, --name NAME  S3 name of the face image to be uploaded. This is what the image will be stored as in S3. If not specified, the filename passed to --file is used instead.
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout (in seconds) for the stream to timeout after not finding a face during comparison
                        Used with -a compare, default is 20
  -p PROFILE, --profile PROFILE
                        Username to perform the -a action upon. Result depends on the action chosen
  -m, --maintain        If this parameter is set, the gesture recognition project will not be shutdown after rekognition is complete (only applicable with -a create,gesture,edit)
```

### How to use it?

Depending on the actions you wish to take (e.g. create, edit, delete compare or gesture), you need to pass certain parameters to the script in order for it to complete successfully. For example, to `create` a new user called `foobar`, you will need to pass the profile's username, lock & unlock combinations, face and `create` action. Like so:

*Note: The paths to files must be absolute paths*

```
python manager.py -a create -f /Users/someuser/Documents/myFace.jpg -p foobar -l /Users/someuser/Documents/my_lock_gesture_1.jpg /Users/someuser/Documents/my_lock_gesture_2.jpg /Users/someuser/Documents/my_lock_gesture_3.jpg /Users/someuser/Documents/my_lock_gesture_4.jpg /Users/someuser/Documents/my_lock_gesture_5.jpg -u /Users/someuser/Documents/my_unlock_gesture_1.jpg /Users/someuser/Documents/my_unlock_gesture_2.jpg /Users/someuser/Documents/my_unlock_gesture_3.jpg /Users/someuser/Documents/my_unlock_gesture_4.jpg /Users/someuser/Documents/my_unlock_gesture_5.jpg
```

Some actions are optional and provide helpful configurable options for the user. For example, the `-t` option will extend the timeout of the Kinesis facial recognition in case slow or unstable connections are expected.

### How it works?

The scripts use the [AWS boto3 SDK for Python](https://github.com/boto/boto3) that allows them to communicate with the AWS services that conduct the recognition and store the user data. The main job of the library is to parse and operate on data returned from boto3 that may not reach the frontend of the applications, being in a sort of helper position usually filled by a nodejs or php server.

Once the scripts have finished carrying out their tasks, they will produce a `response.json` file in this directory with the details of how the script performed. This makes it easier for separate applications not running a Python engine to reliably parse the response of the script.

The structure will always be the same, no matter the operation or amount of debug log the script produced. For example, running a face comparison with a source image and the stored image for the user `morgan`, produces this response:

```json
{
  "TYPE": "SUCCESS | ERROR (the result of the script in a single word)",
  "MESSAGE": "Input face /Users/morgan/Downloads/morgan.jpg matched successfully with stored user's morgan face (a short explanation detailing what the result was)",
  "CONTENT": "null (null, if it's not needed, or a longer explanation or large object that would be useful in debugging what the problem is or investigating further the object of a success)",
  "CODE": 0
}
```

The response file will also provide an exit `CODE` value that the script escaped with in integer format. Anything other than `0` is considered an unsuccessful exit. See [Codes](#Codes) for what each code stands for.

## Codes

No matter the script, all will exit with one of the following codes. For more information on any errors, check the `MESSAGE` and `CONTENT` fields of the response file.

0. Successful exit
1. General Error
2. Something Wasn't Found
3. Something Failed To Upload
4. Something Failed To Delete
5. Kinesis stream Failed To Start
6. Kinesis stream Failed to Die (how dare it)
7. File Is Of An Incompatible Type
8. File Does Not Exist Locally
9. File Does Not Exist In S3
10. Stream Timeout Was Fired or face found did not match
11. Stream Wasn't Found
12. Stream Was Interrupted
13. Invalid Action Type
14. Custom Label Project Failed To Start
15. Custom Label Project Failed To Start Within The Timeout
16. Custom Label Project Failed To Die (How incredibly rude that it's not allowed to live)
17. No recognised gesture was detected
18. Gesture was detected but it was not in the user's combination and/or in in the right position of the user's combination
19. Stream Timeout Failed To Fire
20. Rule Violation: All gestures of the specific locktype are the same
21. Rule Violation: The locking gesture is the same as the unlocking gesture
22. Rule Violation: One gesture combination is the same as the other when reversed
23. Custom Label Project is shutting down or starting up
24. Given image is too large for detection of custom labels
25. ClientError on image processing of custom labels. Likelihood is too large to even send with detect_custom_labels
26. User gesture combination api is rate-limited
27. Captured face in stream does not match the user's face
28. Rule Violation: Given gesture combination for the specific locktype is too short (minimum combination length = 4)
