# Testing various python gesture libraries

On GitHub, there are plenty of [pythonic gesture recognition libraries](https://github.com/topics/gesture-recognition?l=python) but all seemed unstable and/or hard to upscale and adapt to my purposes.
Unlike the `face_recog_test.py`, there is not an easily downloadable gesture recognition library for Python that I could find. This is one of the reasons why I gravitated away from using local libs over a cloud solution.

Below are the local libraries I tried to make work for my solution with pros (**+**) and cons (**-**) for each of them. I have deleted to contents to save making duplicates of them but left the README's in their original states of when I was working on them:

## [20bn-realtimenet](20bn-realtimenet/)

- **+** High accuracy of the algorithm. Easy to setup.
- **-** No room for expansion and requires a virtual environment which I don't have much knowledge of. Also requires `PYTHONPATH` manipulation which can be messy.

## [Real-time-GesRec](Real-time-GesRec/)

- **+** Works very well for video streams. Lots of pretrained models to play with so I wouldn't need to make my own. Provides a good metadata output.
- **-** Doesn't actually classify a gesture, it just pumps the metadata (location, size, colour etc) of a gesture that is made to a graph. Hard to install and setup, there are lots of dependancies that are needed. Seems a very heavy package for something relatively simple.

## [Unified-Gesture-and-Fingertip-Detection](https://github.com/MahmudulAlam/Unified-Gesture-and-Fingertip-Detection)

- **+** Works on videos (not streams sadly) and images. Very accurate, can pick up specific fingers so a user wouldn't have to make a gesture combination very complex.
- **-** Documentation is rather lacking regarding installation requirements ([although I have tried to make it better](https://github.com/MahmudulAlam/Unified-Gesture-and-Fingertip-Detection/pull/11/)). Not updated often. No room or advice on how to expand to my own datasets.
