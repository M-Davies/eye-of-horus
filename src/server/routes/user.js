var express = require("express")
var router = express.Router()
var spawn = require('child_process').spawn
var fs = require('fs')
var cors = require('cors')
var AWS = require('aws-sdk')

var S3 = new AWS.S3()

router.use(cors())

function readResponse() {
    return JSON.parse(fs.readFileSync("response.json", "utf-8"))
}

router.post("/exists", function(req, res, next) {
    console.log(`return body on server side = ${req.body.user}`)
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
            Error(err)
        }
    })
})

router.post("/create", function(req, res, next) {
    let response = null
    let logs = null

    // Extract gesture arrays
    const splitLock = Array.from(req.body.lock)
    const splitUnlock = Array.from(req.body.unlock)

    // Execute creation script with params given
    const createRequest = spawn("python", [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`,
        "-m", "-a", "create",
        "-p", `${req.body.user}`,
        "-f", `${req.body.face}`,
        "-l", `${splitLock.join(" ")}`,
        "-u", `${splitUnlock.join(" ")}`
    ])
    // Collect data from script, usually python's stdout that redirects to stderr for some reason
    createRequest.stderr.on('data', function (data) {
        logs += "\n" + data.toString()
    })
    // On close event we are sure that stream from child process is closed, read response file
    createRequest.on('close', (code) => {
        console.log(`child process close all stdio with code ${code}`);
    })

    // TODO: Parse response from the script
    response = readResponse()
    res.send(response)
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
        console.log(`child process close all stdio with code ${code}`);
    })

    // TODO: Parse response from the script
    response = readResponse()
    res.send(response)
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
        console.log(`child process close all stdio with code ${code}`);
    })

    // TODO: Parse response from the script
    response = readResponse()
    res.send(response)
})

module.exports = router;
