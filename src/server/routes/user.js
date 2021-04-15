var express = require("express")
var router = express.Router()
var spawn = require('child_process').spawn
var fs = require('fs')
var cors = require('cors')
var AWS = require('aws-sdk')

var S3 = new AWS.S3()

router.use(cors())

function readResponse() {
    try {
        return JSON.parse(fs.readFileSync(`${process.env.ROOT_DIR}/src/scripts/response.json`))
    } catch (err) {
        return false
    }
}

router.post("/exists", function(req, res, next) {
    console.log(`Executed exists endpoint with username ${req.body.user}`)
    // Connect to AWS to check if user exists
    S3.getObjectAcl({
        Bucket: process.env.FACE_RECOG_BUCKET,
        Key: `users/${req.body.user}/${req.body.user}.jpg`
    }, function(err, data) {
        if (data && !err) {
            // User exists
            res.status(200).send(true)
        } else if (err.statusCode === 404) {
            // User doesn't exist
            res.status(200).send(false)
        } else {
            // Something more serious went wrong
            res.status(500).send(err.message)
        }
    })
})

router.post("/create", function(req, res, next) {
    // Verify req params
    if (!req.body.user) {
        res.status(400).send("Invalid username supplied")
    } else if (!req.body.face) {
        res.status(400).send("Invalid face path supplied")
    } else if (!req.body.locks || Object.keys(req.body.locks).length <= 0) {
        res.status(400).send("Invalid lock paths supplied")
    } else if (!req.body.unlocks || Object.keys(req.body.unlocks).length <= 0) {
        res.status(400).send("Invalid unlock paths supplied")
    }

    let response = null
    let logs = null
    const lockGestures = Array.from((req.body.locks).split(","))
    const unlockGestures = Array.from((req.body.unlocks).split(","))

    // Execute creation script with params given
    let args = [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`, "-m", "-a", "create", "-p", `${req.body.user}`,
        "-n", `${req.body.user}.jpg`,
        "-f", `${req.body.face}`, "-l"
    ]
    lockGestures.forEach(gesture => {
        args.push(gesture)
    })
    args.push("-u")
    unlockGestures.forEach(gesture => {
        args.push(gesture)
    })

    const createRequest = spawn("python", args)

    // On error event, something has gone wrong early so read response file if exists or exit with error
    createRequest.on('error', function(err) {
        console.log(`child process errored with message: ${err}`)
        response = readResponse()
        if (response === false) {
            res.sendStatus(500)
        } else {
            res.status(400).send(response)
        }
    })
    // Collect data from script
    createRequest.stdout.on('data', function (data) {
        logs += "\n" + data.toString()
    })
    // On close event we are sure that stream from child process is closed, read response file
    createRequest.on('close', (code) => {
        console.log(`Child process close all stdio with code ${code}\nLogs collected:\n${logs}`)

        // Read response file if exists
        response = readResponse()
        if (response === false) {
            res.sendStatus(500)
        }

        // If error was thrown by python, return the corresponding code. Otherwise, return 201 Created
        if (response.TYPE === "ERROR") {
            res.status(400).send(response)
        } else {
            res.sendStatus(201)
        }
    })
})

router.post("/login", function(req, res, next) {
    // Verify req params
    if (!req.body.user) {
        res.status(400).send("Invalid username supplied")
    } else if (!req.body.face) {
        res.status(400).send("Invalid face path supplied")
    } else if (!req.body.unlocks || Object.keys(req.body.unlocks).length <= 0) {
        res.status(400).send("Invalid unlock paths supplied")
    }

    let faceResponse = null
    let faceLogs = null

    // Authenticate face
    const faceArgs = [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`, "-m", "-a", "compare",
        "-f", `${req.body.face}`, "-p", `${req.body.user}`
    ]
    const faceRequest = spawn("python", faceArgs)

    // On error event, something has gone wrong early so read response file if exists or exit with error
    faceRequest.on('error', function(err) {
        console.log(`Face child process errored with message: ${err}`)
        faceResponse = readResponse()
        if (faceResponse === false) {
            res.sendStatus(500)
        } else {
            res.status(400).send(faceResponse)
        }
    })
    // Collect data from script
    faceRequest.stdout.on('data', function (data) {
        faceLogs += "\n" + data.toString()
    })
    // On close event we are sure that stream from child process is closed, read response file
    faceRequest.on('close', (code) => {
        console.log(`Face child process close all stdio with code ${code}\nLogs collected:\n${faceLogs}`)

        // Read response file if exists
        faceResponse = readResponse()
        if (faceResponse === false) {
            res.status(500).send("Internal server error")
        } else if (faceResponse.TYPE === "ERROR") {
            // If error was thrown by python, return the corresponding code. Otherwise, check if the right face was found
            res.status(400).send(faceResponse)
        } else if (faceResponse.TYPE === "SUCCESS") {
            let gestureResponse = null
            let gestureLogs = null

            // Authenticate gestures
            const gestureArgs = [
                `${process.env.ROOT_DIR}/src/scripts/manager.py`, "-m", "-a", "gesture", "-p", `${req.body.user}`, "-u"
            ]
            const unlockGestures = Array.from((req.body.unlocks).split(","))
            unlockGestures.forEach(gesture => {
                gestureArgs.push(gesture)
            })
            const gestureRequest = spawn("python", gestureArgs)

            // On error event, something has gone wrong early so read response file if exists or exit with error
            gestureRequest.on('error', function(err) {
                console.log(`Gesture child process errored with message: ${err}`)
                gestureResponse = readResponse()
                if (gestureResponse === false) {
                    res.sendStatus(500)
                } else {
                    res.status(400).send(gestureResponse)
                }
            })
            // Collect data from script
            gestureRequest.stdout.on('data', function (data) {
                gestureLogs += "\n" + data.toString()
            })
            // On close event we are sure that stream from child process is closed, read response file
            gestureRequest.on('close', (code) => {
                console.log(`Gesture child process close all stdio with code ${code}\nLogs collected:\n${gestureLogs}`)
                // Read response file if exists
                gestureResponse = readResponse()
                if (gestureResponse === false) {
                    res.sendStatus(500)
                }

                // If error was thrown by python, return the corresponding code. Otherwise, attempt authentication with the given gestures
                if (gestureResponse.TYPE === "ERROR") {
                    res.status(400).send(gestureResponse)
                } else {
                    res.sendStatus(200)
                }
            })
        } else {
            res.status(500).send("Server error")
        }
    })
})

router.post("/logout", function(req, res, next) {
    let response = null
    let logs = null

    // Extract gesture arrays & execute request
    let logoutRequest = null
    const splitLock = Array.from(req.body.lock)
    logoutRequest = spawn("python", [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`,
        "-m", "-a", "gesture",
        "-p", `${req.body.user}`,
        "-f", `${req.body.face}`,
        "-l", `${splitLock.join(" ")}`
    ])

    // Collect data from script, usually python's stdout that redirects to stderr for some reason
    logoutRequest.stderr.on('data', function (data) {
        logs += "\n" + data.toString()
    })
    // On close event we are sure that stream from child process is closed, read response file
    logoutRequest.on('close', (code) => {
        console.log(`child process close all stdio with code ${code}\nlogs collected:\n${logs}`)
    })

    // TODO: Parse response from the script
    response = readResponse()
    res.send(response)
})

module.exports = router;
