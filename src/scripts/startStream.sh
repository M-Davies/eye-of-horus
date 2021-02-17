#!/bin/zsh

# Check if stream is already running (excluding the grep process and consoleout from the result)
ps | grep "gst-launch-1.0" | grep -v grep &> /dev/null
ret=$?

# Stream is not running
if [ $ret -eq 1 ]; then
    echo "############################################"
    echo "[INFO] STARTING AWS KINESIS VIDEO STREAM!"
    echo "############################################"

    # Get role stream keys from .env
    export $(egrep -v '^#' $PWD/../../.env | xargs)

    # Start streaming to aws in background
    gst-launch-1.0 avfvideosrc device-index=0 ! videoconvert ! video/x-raw,format=I420,width=640,height=480,framerate=20/1 ! x264enc bframes=0 key-int-max=65 bitrate=300 ! video/x-h264,stream-format=avc,alignment=au,profile=baseline ! kvssink stream-name="CameraVideoStream" storage-size=512 access-key="${ACCESS_KEY}" secret-key="${SECRET_KEY}" aws-region="eu-west-1" &

    echo "[SUCCESS] Stream is running!"
    exit 0

# Stream is already running
elif [ $ret -eq 0 ]; then
    echo "[SUCCESS] Stream is already running! Exiting..."
    exit 0

# Something went wrong with ps or grep
else
    echo "[ERROR] Unable to determine if stream exists. Something went wrong with the searching logic itself"
    exit $ret
fi
