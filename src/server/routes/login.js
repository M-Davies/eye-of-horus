var express = require("express")
var router = express.Router()
var cors = require('cors')
var AWS = require('aws-sdk')

var S3 = new AWS.S3()

router.use(cors())

router.post("/exists", function(req, res, next) {
    // Connect to AWS to check if user exists
    return S3.getObjectAcl({
        Bucket: process.env.FACE_RECOG_BUCKET,
        Key: `users/${req.body.username}/${req.body.username}.jpg`
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

module.exports = router;
