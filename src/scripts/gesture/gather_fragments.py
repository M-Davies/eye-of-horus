# -----------------------------------------------------------
# Collects frames from the video stream
#
# Copyright (c) 2021 Morgan Davies, UK
# Released under MIT License
# -----------------------------------------------------------

import boto3

import cv2
import os
import sys
import datetime
sys.path.append(os.path.dirname(__file__) + "/..")
import commons
import run_gesture_recog

#########
# START #
#########
def main(argv):
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
        commons.throw("ERROR", f"Stream URL was not valid or stream wasn't found. Try restarting the stream and trying again", 3)

    vcap = cv2.VideoCapture(streamUrl)
    frames = []
    frameCount = 1
    while(vcap.isOpened()):

        # Capture frame-by-frame
        ret, frame = vcap.read()

        if frame is not None:
            # Only capture every other frame to save space and time
            if frameCount & 1 == True:
                frames.append(frame)

            frameCount += 1

            # Display the resulting frame
            # cv2.imshow('frame',frame)

            # Press q to close the video windows before it ends if you want
            # if cv2.waitKey(22) & 0xFF == ord('q'):
                # break
        else:
            print("Stream Interrupted! Stopping gathering...")
            break

    # When everything done, release the capture
    vcap.release()
    cv2.destroyAllWindows()
    print("Video stop")
    print(frames)

if __name__ == "__main__":
    main(sys.argv[1:])
