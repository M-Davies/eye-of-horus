# Testing face_recognition.py

https://github.com/ageitgey/face_recognition

## Feedback

The lib is powerful and serves the purposes I have for my project. It will be sufficient and I especially like the example code that can be easily reused for my project. However, there are some concerns...

- I will need to keep in mind that the lib is sensitive to glasses and other jewellery (so a user will need to be reminded to remove them when taking their picture)
- The program is (obviously) in Python which will conflict with the NodeJS website application that will be powering the frontend.
- The accuracy and confidence levels of the lib are unknown where big cloud face comparison services (e.g. Amazon Rekognition) outright tell you what they are.
- Finally, and most importantly, the library's `known_face_names` / `known_face_encodings` only works as lists and not as maps so the process of retrieving a user's data from the backend, testing it and moving onto the next one may be quite slow with poor internet connections.
