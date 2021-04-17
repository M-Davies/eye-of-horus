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
    if (req.body.user === undefined) {
        res.status(400).send("Invalid username supplied")
    }

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
    if (req.body.user === undefined) {
        res.status(400).send("Invalid username supplied")
    } else if (req.body.face === undefined) {
        res.status(400).send("Invalid face path supplied")
    } else if (req.body.locks === undefined) {
        res.status(400).send("Invalid lock paths supplied")
    } else if (req.body.unlocks === undefined) {
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

router.post("/auth", function(req, res, next) {
    // Verify req params
    if (req.body.user === undefined) {
        res.status(400).send("No username supplied")
    } else if (req.body.face === undefined) {
        res.status(400).send("No face path supplied")
    } else if (req.body.locks === undefined && req.body.unlocks === undefined) {
        res.status(400).send("No gesture paths supplied")
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
    faceRequest.stderr.on('data', function (data) {
        console.log("STDERR")
        console.log(data.toString())
    })
    // On close event we are sure that stream from child process is closed, read response file
    faceRequest.on('close', (code) => {
        const badCreds = `Incorrect face or gesture combination given for ${req.body.user}`
        console.log(`Face child process close all stdio with code ${code}\nLogs collected:\n${faceLogs}`)

        // Read response file if exists
        faceResponse = readResponse()
        if (faceResponse === false) {
            res.status(500).send("Internal server error")
        } else if (faceResponse.TYPE === "ERROR") {
            // If error was thrown by python (usually if the faces don't match), return the corresponding code.
            res.status(400).send(badCreds)
        } else if (faceResponse.TYPE === "SUCCESS") {
            let gestureResponse = null
            let gestureLogs = null

            // Authenticate gestures
            let gestureArgs = [`${process.env.ROOT_DIR}/src/scripts/manager.py`, "-m", "-a", "gesture", "-p", `${req.body.user}`]

            if (req.body.locks) {
                gestureArgs.push("-l")
                Array.from((req.body.locks).split(",")).forEach(gesture => {
                    gestureArgs.push(gesture)
                })
            } else {
                gestureArgs.push("-u")
                Array.from((req.body.unlocks).split(",")).forEach(gesture => {
                    gestureArgs.push(gesture)
                })
            }
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

                // If error was thrown by python (usually if the gesture combination is wrong), return the corresponding code.
                if (gestureResponse.TYPE === "ERROR") {
                    res.status(400).send(badCreds)
                } else {
                    res.sendStatus(200)
                }
            })
        } else {
            res.status(500).send("Server error")
        }
    })
})

router.post("/edit", function(req, res, next) {
    let response = null
    let logs = null

    // Verify req params
    let lockNoFiles = null
    let unlockNoFiles = null
    try {
        lockNoFiles = Object.keys(req.body.locks).length <= 0
    } catch (err) {
        lockNoFiles = true
    }
    try {
        unlockNoFiles = Object.keys(req.body.unlocks).length <= 0
    } catch (err) {
        unlockNoFiles = true
    }

    if (req.body.user === undefined) {
        res.status(400).send("No username supplied")
    } else if (req.body.face === undefined && lockNoFiles === true && unlockNoFiles === true) {
        res.status(400).send("No editable objects supplied")
    }

    let args = [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`, "-m", "-a", "edit", "-p", `${req.body.user}`,
        "-n", `${req.body.user}.jpg`
    ]
    if (req.body.face) {
        args.push("-f")
        args.push(req.body.face)
    }
    if (!lockNoFiles) {
        args.push("-l")
        Array.from((req.body.locks).split(",")).forEach(gesture => {
            args.push(gesture)
        })
    }
    if (!unlockNoFiles) {
        args.push("-u")
        Array.from((req.body.unlocks).split(",")).forEach(gesture => {
            args.push(gesture)
        })
    }
    const request = spawn("python", args)

    request.on('error', function(err) {
        console.log(`Edit child process errored with message: ${err}`)
        response = readResponse()
        if (response === false) {
            res.sendStatus(500)
        } else {
            res.status(400).send(response)
        }
    })

    request.stdout.on('data', function (data) {
        logs += "\n" + data.toString()
    })

    request.on('close', (code) => {
        console.log(`Edit child process close all stdio with code ${code}\nLogs collected:\n${logs}`)
        response = readResponse()
        if (response === false) {
            res.sendStatus(500)
        }

        if (response.TYPE === "ERROR") {
            res.status(400).send(response)
        } else {
            res.sendStatus(201)
        }
    })
})

router.post("/delete", function(req, res, next) {
    let response = null
    let logs = null

    // Verify req params
    if (req.body.user === undefined) {
        res.status(400).send("No username supplied")
    }

    let args = [`${process.env.ROOT_DIR}/src/scripts/manager.py`, "-m", "-a", "delete", "-p", `${req.body.user}`]
    const request = spawn("python", args)

    request.on('error', function(err) {
        console.log(`Delete child process errored with message: ${err}`)
        response = readResponse()
        if (response === false) {
            res.sendStatus(500)
        } else {
            res.status(400).send(response)
        }
    })

    request.stdout.on('data', function (data) {
        logs += "\n" + data.toString()
    })

    request.on('close', (code) => {
        console.log(`Delete child process close all stdio with code ${code}\nLogs collected:\n${logs}`)
        response = readResponse()
        if (response === false) {
            res.sendStatus(500)
        }

        if (response.TYPE === "ERROR") {
            res.status(400).send(response)
        } else {
            res.sendStatus(200)
        }
    })
})

module.exports = router;
