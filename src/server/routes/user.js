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
        return JSON.parse(fs.readFileSync(`${process.env.ROOT_DIR}/src/scripts/response.json`, "utf-8"))
    } catch (err) {
        return false
    }
}

router.post("/exists", function(req, res, next) {
    console.log(`executed exists endpoint with username ${req.body.user}`)
    // Connect to AWS to check if user exists
    S3.getObjectAcl({
        Bucket: process.env.FACE_RECOG_BUCKET,
        Key: `users/${req.body.user}/${req.body.user}.jpg`
    }, function(err, data) {
        if (data && !err) {
            // User exists
            res.send(true)
        } else if (err.statusCode === 404) {
            // User doesn't exist
            res.send(false)
        } else {
            // Something more serious went wrong
            throw new Error(err.message)
        }
    })
})

router.post("/create", function(req, res, next) {
    let response = null
    let logs = null

    console.log("BODY CONTENTS")
    console.log(req.body)

    // Execute creation script with params given
    const createRequest = spawn("python", [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`,
        "-m", "-a", "create",
        "-p", `${req.body.user}`,
        "-f", `${req.body.face}`,
        "-l", `${(req.body.locks).replace(",", " ")}`,
        "-u", `${(req.body.unlocks).replace(",", " ")}`
    ])

    // On error event, something has gone wrong early so read response file if exists or exit with error
    createRequest.on('error', function(err) {
        console.log(`child process errored with message: ${err}`)
        response = readResponse()
        if (!response) {
            res.sendStatus(500)
        } else {
            res.sendStatus(response.code)
        }
    })
    // Collect data from script, sometimes python's stdout redirects to stderr for some reason
    createRequest.stdout.on('data', function (data) {
        logs += "\n" + data.toString()
    })
    createRequest.stderr.on('data', function (data) {
        logs += "\n" + data.toString()
    })
    // On close event we are sure that stream from child process is closed, read response file
    createRequest.on('close', (code) => {
        console.log(`child process close all stdio with code ${code}\nlogs collected:\n${logs}`)
    })

    // Read response file if exists
    response = readResponse()
    if (!response) res.sendStatus(500)

    console.log(`child process produced response file`)
    console.log(response)

    // If error was thrown by python, return the corresponding code. Otherwise, return 201 Created
    if (response.messageType === "ERROR") {
        res.sendStatus(response.code)
    } else {
        res.sendStatus(201)
    }
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
    if (response.messageType === "ERROR") {
        res.sendStatus(response.code)
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
