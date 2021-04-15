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
    let response = null
    let logs = null

    console.log("BODY CONTENTS")
    console.log(req.body)

    const lockGestures = Array.from((req.body.locks).split(","))
    const unlockGestures = Array.from((req.body.unlocks).split(","))
    console.log("GESTURES")
    console.log(lockGestures)
    console.log(unlockGestures)

    // Execute creation script with params given
    let args = [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`, "-m", "-a", "create", "-p", `${req.body.user}`,
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
        console.log("stdout out")
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

        console.log(`child process produced response file`)
        console.log(response)

        // If error was thrown by python, return the corresponding code. Otherwise, return 201 Created
        if (response.TYPE === "ERROR") {
            res.status(400).send(response)
        } else {
            res.sendStatus(201)
        }
    })
})

router.post("/login", function(req, res, next) {
    let response = null
    let logs = null

    // Extract gesture arrays & execute request
    let loginRequest = null
    const splitUnlock = Array.from(req.body.unlock)
    loginRequest = spawn("python", [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`,
        "-m", "-a", "gesture",
        "-p", `${req.body.user}`,
        "-f", `${req.body.face}`,
        "-u", `${splitUnlock.join(" ")}`
    ])

    // Collect data from script, usually python's stdout that redirects to stderr for some reason
    loginRequest.stderr.on('data', function (data) {
        logs += "\n" + data.toString()
    })
    // On close event we are sure that stream from child process is closed, read response file
    loginRequest.on('close', (code) => {
        console.log(`child process close all stdio with code ${code}\nlogs collected:\n${logs}`)
    })

    // Read response file
    response = readResponse()
    console.log(`child process produced response file ${response}`)

    // If error was thrown by python, return the corresponding code. Otherwise, return 200 Success
    if (response.TYPE === "ERROR") {
        res.status(400).send(response)
    } else {
        res.sendStatus(200)
    }
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
