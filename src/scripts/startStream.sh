#!/bin/zsh
# Get role stream keys from .env
export $(egrep -v '^#' $PWD/../../.env | xargs)

# Start streaming to aws
gst-launch-1.0 avfvideosrc device-index=0 ! videoconvert ! video/x-raw,format=I420,width=640,height=480,framerate=20/1 ! x264enc bframes=0 key-int-max=65 bitrate=300 ! video/x-h264,stream-format=avc,alignment=au,profile=baseline ! kvssink stream-name="CameraVideoStream" storage-size=512 access-key="${ACCESS_KEY}" secret-key="${SECRET_KEY}" aws-region="eu-west-1"
