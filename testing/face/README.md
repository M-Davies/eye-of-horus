# Notes

**[OtherExploredSoloutions/](OtherExploredSoloutions/) contains my tinkering with the [face_recognition](https://github.com/ageitgey/face_recognition) python lib and is seperate to what I will discussing here.**

My notes and investigations into creating a streamed, rekognition cloud service using the AWS CLI SDK. This was done for testing and experimetation purposes, with the final product's interaction with AWS being done using the Python SDK (see [scripts/](../../scripts)).

ARN's and other sensetive info has been omitted but you can generally observe how I constructed the service, following these guides in order:

1. https://docs.aws.amazon.com/rekognition/latest/dg/setting-up-your-amazon-rekognition-streaming-video-resources.html
2. https://docs.aws.amazon.com/rekognition/latest/dg/streaming-using-gstreamer-plugin.html
3. https://docs.aws.amazon.com/streams/latest/dev/fundamental-stream.html#get-records
4. https://docs.aws.amazon.com/rekognition/latest/dg/streaming-video-kinesis-output.html

## Created an S3 bucket

Created an [AWS S3 bucket](https://s3.console.aws.amazon.com/s3/buckets) to act as a sudo database to store authorised faces.

I still needed to link the faces from S3 to a local collection, which is done via indexing:

## Index faces in S3

Adds faces from the database in S3 to the collection client

```bash
aws rekognition index-faces \
  --image '{"S3Object":{"Bucket":"eye-of-horus-face-recognition","Name":"FacialRecognition/morgan.jpg"}}' \
  --collection-id "RekognitionCollection" \
  --max-faces 1 \
  --quality-filter "AUTO" \
  --detection-attributes "ALL" \
  --external-image-id "morgan.jpg"
```

## Create & Start Rekognition stream processor

Combines the data and video streams and handles the rekognition side:

```bash
aws rekognition create-stream-processor \
    --input '{"KinesisVideoStream" : {"Arn":"`arn-of-video-streamer`"}}' \
    --stream-processor-output '{"KinesisDataStream" : {"Arn":"`arn-of-data-streamer`"}}' \
    --name "CameraStreamProcessor" \
    --settings --settings '{"FaceSearch":{"CollectionId":"RekognitionCollection", "FaceMatchThreshold":"90"}}' \
    --role-arn "`arn-of-role`"

aws rekognition start-stream-processor --name "CameraStreamProcessor"
```

## DEVICE INFO OUTPUT

Now the rekognition side is setup, I will now setup my GStreamer plugin, allowing me to stream to the Kinesis bucket [I created earlier](#Notes).

First, I call the built in device monitor to understand what my video camera specs were:

```bash
$ gst-device-monitor-1.0

Probing devices...

Device found:

 name  : FaceTime HD Camera (Built-in)
 class : Video/Source
 caps  : video/x-raw(memory:GLMemory), width=1280, height=720, format=UYVY, framerate={ (fraction)10000000/333333, (fraction)10000000/344827, (fraction)5000000/178571, (fraction)1000000/37037, (fraction)2000000/76923, (fraction)25/1, (fraction)5000000/208333, (fraction)5000000/217391, (fraction)2000000/90909, (fraction)1000000/47619, (fraction)20/1, (fraction)2000000/105263, (fraction)2000000/111111, (fraction)2000000/117647, (fraction)16/1, (fraction)5000000/333333, (fraction)2000000/142857, (fraction)1000000/76923, (fraction)10000000/833333, (fraction)1000000/90909, (fraction)10/1, (fraction)10000000/1111111, (fraction)8/1, (fraction)10000000/1428571, (fraction)5000000/833333, (fraction)5/1, (fraction)4/1, (fraction)10000000/3333333, (fraction)2/1, (fraction)1/1 }, texture-target=rectangle
         video/x-raw(memory:GLMemory), width=640, height=480, format=UYVY, framerate={ (fraction)10000000/333333, (fraction)10000000/344827, (fraction)5000000/178571, (fraction)1000000/37037, (fraction)2000000/76923, (fraction)25/1, (fraction)5000000/208333, (fraction)5000000/217391, (fraction)2000000/90909, (fraction)1000000/47619, (fraction)20/1, (fraction)2000000/105263, (fraction)2000000/111111, (fraction)2000000/117647, (fraction)16/1, (fraction)5000000/333333, (fraction)2000000/142857, (fraction)1000000/76923, (fraction)10000000/833333, (fraction)1000000/90909, (fraction)10/1, (fraction)10000000/1111111, (fraction)8/1, (fraction)10000000/1428571, (fraction)5000000/833333, (fraction)5/1, (fraction)4/1, (fraction)10000000/3333333, (fraction)2/1, (fraction)1/1 }, texture-target=rectangle
         video/x-raw, width=1280, height=720, format={ (string)UYVY, (string)YUY2, (string)NV12, (string)BGRA }, framerate={ (fraction)1/1, (fraction)2/1, (fraction)10000000/3333333, (fraction)4/1, (fraction)5/1, (fraction)5000000/833333, (fraction)10000000/1428571, (fraction)8/1, (fraction)10000000/1111111, (fraction)10/1, (fraction)1000000/90909, (fraction)10000000/833333, (fraction)1000000/76923, (fraction)2000000/142857, (fraction)5000000/333333, (fraction)16/1, (fraction)2000000/117647, (fraction)2000000/111111, (fraction)2000000/105263, (fraction)20/1, (fraction)1000000/47619, (fraction)2000000/90909, (fraction)5000000/217391, (fraction)5000000/208333, (fraction)25/1, (fraction)2000000/76923, (fraction)1000000/37037, (fraction)5000000/178571, (fraction)10000000/344827, (fraction)10000000/333333 }
         video/x-raw, width=640, height=480, format={ (string)UYVY, (string)YUY2, (string)NV12, (string)BGRA }, framerate={ (fraction)1/1, (fraction)2/1, (fraction)10000000/3333333, (fraction)4/1, (fraction)5/1, (fraction)5000000/833333, (fraction)10000000/1428571, (fraction)8/1, (fraction)10000000/1111111, (fraction)10/1, (fraction)1000000/90909, (fraction)10000000/833333, (fraction)1000000/76923, (fraction)2000000/142857, (fraction)5000000/333333, (fraction)16/1, (fraction)2000000/117647, (fraction)2000000/111111, (fraction)2000000/105263, (fraction)20/1, (fraction)1000000/47619, (fraction)2000000/90909, (fraction)5000000/217391, (fraction)5000000/208333, (fraction)25/1, (fraction)2000000/76923, (fraction)1000000/37037, (fraction)5000000/178571, (fraction)10000000/344827, (fraction)10000000/333333 }
  properties:
    device.api = avf
    avf.unique_id = 0x8020000005ac8514
    avf.model_id = "UVC\ Camera\ VendorID_1452\ ProductID_34068"
    avf.has_flash = false
    avf.has_torch = false
    avf.manufacturer = "Apple\ Inc."
  gst-launch-1.0 avfvideosrc device-index=0 ! ...
```

## G Streamer Start

Start streaming to Kinesis and begin rekognition.

### High Performance

```bash
gst-launch-1.0 avfvideosrc device-index=0 ! videoconvert ! video/x-raw,format=I420,width=1280,height=720,framerate=20/1 ! x264enc bframes=0 key-int-max=45 bitrate=500 ! video/x-h264,stream-format=avc,alignment=au,profile=baseline ! kvssink stream-name="CameraVideoStream" storage-size=512 access-key="access-key" secret-key="access-key-secret" aws-region="eu-west-1"
```

### Cuts down latency

RESULT = Cuts it by about 2-5 seconds

```bash
gst-launch-1.0 avfvideosrc device-index=0 ! videoconvert ! video/x-raw,format=I420,width=640,height=480,framerate=20/1 ! x264enc bframes=0 key-int-max=65 bitrate=300 ! video/x-h264,stream-format=avc,alignment=au,profile=baseline ! kvssink stream-name="CameraVideoStream" storage-size=512 access-key="access-key" secret-key="access-key-secret" aws-region="eu-west-1"
```

## Retrieving Rekognition Results

While the stream is running, pull the rekognition results from the processor running on the Kinesis stream:

### Retrieve the shards from the kinesis stream**

List all the [shards](https://docs.aws.amazon.com/streams/latest/dev/key-concepts.html#high-level-architecture) (essentially collections of frames captured from the stream):

```bash
aws kinesis list-shards --stream-name AmazonRekognitionCameraDataStream --shard-filter '{"Type":"AT_LATEST"}'
```

We can then iterate through the JSON, creating a shard iterator for each shard-id, allowing us to retrieve the records:

### Create a shard iterator and read results

Both of these methods are basically the same, except [Latest](#Latest) is usually quicker since you don't have to calculate the timestamp for each iteration.

Both of these return a base64 encoded video analysis, containing information on face detections and the stream that is running. It will sometimes return records straight away, other times it will return no records but a next shard value that DOES return records.

#### Timestamp

```bash
SHARD_ITERATOR=$(aws kinesis get-shard-iterator --shard-id [shard_id_from_list-shards] --shard-iterator-type AT_TIMESTAMP --timestamp [current_timestamp] --stream-name AmazonRekognitionCameraDataStream --query 'ShardIterator')
    aws kinesis get-records --shard-iterator $SHARD_ITERATOR
```

#### Latest

```bash
SHARD_ITERATOR=$(aws kinesis get-shard-iterator --shard-id [shard_id_from_list-shards] --shard-iterator-type LATEST --stream-name AmazonRekognitionCameraDataStream --query 'ShardIterator')
    aws kinesis get-records --shard-iterator $SHARD_ITERATOR
```
