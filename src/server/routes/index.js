var express = require('express')
var router = express.Router()
var fileUpload = require('express-fileupload')
var fs = require("fs")
var spawn = require('child_process').spawn

router.use(fileUpload())

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Express' })
})

router.post('/upload/file', function(req, res, next) {
  // Verify req params
  if (req.files === undefined || Object.keys(req.files).length <= 0) {
    res.status(400).send("No files supplied")
  }

  // Iterate through files and upload one at a time
  let uploadedPaths = []
  Object.keys(req.files).forEach(fileWrapper => {
    let fileObj = req.files[fileWrapper]
    console.log(`UPLOADING ${fileObj.name}`)
    let currentFilePath = `${process.env.ROOT_DIR}/src/server/public/${fileObj.name}`

    // Delete old copy if it exists
    try {
      fs.unlinkSync(currentFilePath)
      console.log("Successfully deleted old file");
    } catch (err) {
      if (err && err.code === 'ENOENT') {
        // File doesn't exist
        console.log("Old File doesn't exist, won't remove it.")
      } else {
        // Other errors, e.g. maybe we don't have enough permission
        res.status(500).send("Error occurred while trying to remove file")
      }
    }

    // Upload new
    fileObj.mv(
      currentFilePath,
      function (err) {
        if (err) {
          return res.status(500).send(err)
        }
      }
    )

    console.log(`SUCCESSFULLY UPLOADED ${fileObj.name}`)
    uploadedPaths.push(currentFilePath)
  })

  // Return server side paths to uploaded files
  return res.send(uploadedPaths)
});

router.post('/upload/encoded', function(req, res, next) {
  if (req.body.encoded === undefined) { res.status(500).send("No encoded object uploaded") }
  const path = `${process.env.ROOT_DIR}/src/server/public/${Math.floor((Math.random() * 1000000) + 1).toString()}.jpg`

  // Delete old copy if it exists
  try {
    fs.unlinkSync(path)
    console.log("Successfully deleted old file");
  } catch (err) {
    if (err && err.code === 'ENOENT') {
      // File doesn't exist
      console.log("Old File doesn't exist, won't remove it.")
    } else {
      // Other errors, e.g. maybe we don't have enough permission
      res.status(500).send("Error occurred while trying to remove file")
    }
  }

  // Create new file from data
  const data = req.body.encoded.replace(/^data:image\/\w+;base64,/, "")
  let buffer = new Buffer(data, 'base64')
  fs.writeFile(path, buffer, function(err, result) {
    if (err) {
      return res.status(500).send(err)
    }
  })

  console.log(`SUCCESSFULLY UPLOADED AND CONVERTED CAPTURE TO ${path}`)
  res.status(200).send([path])
})

router.post("/types", function(req, res, next) {
  if (req.body.files === undefined) { res.status(500).send("No files to check for gestures") }

  const files = Array.from((req.body.files).split(","))

  let args = [`${process.env.ROOT_DIR}/src/scripts/gesture/gesture_recog.py`, "-m", "-a", "gesture", "-f"]
  files.forEach(path => {
    args.push(path)
  })

  let response = null
  let logs = null
  const gestureRequest = spawn("python", args)

  gestureRequest.on('error', function(err) {
    console.log(`Gesture types child process errored with message: ${err}`)
    response = JSON.parse(fs.readFileSync(`${process.env.ROOT_DIR}/src/scripts/response.json`))
    if (response === false) {
        res.sendStatus(500)
    } else {
        res.status(400).send(response)
    }
  })

  gestureRequest.stdout.on('data', function (data) {
      logs += "\n" + data.toString()
  })

  gestureRequest.on('close', (code) => {
    console.log(`Gesture types child process close all stdio with code ${code}\nLogs collected:\n${logs}`)
    response = JSON.parse(fs.readFileSync(`${process.env.ROOT_DIR}/src/scripts/response.json`))

    if (response.TYPE === "ERROR") {
      res.status(400).send(response.MESSAGE)
    } else {
      let gestureNames = []
      JSON.parse(response.CONTENT)['GESTURES'].forEach(gestureObj => {
        const filePath = Object.keys(gestureObj)[0]
        try {
          gestureNames.push(gestureObj[filePath]["Name"])
        } catch (err) {
          if (err instanceof TypeError) {
            gestureNames.push("UNKNOWN")
          } else {
            res.status(500).send("Failed to parse response content object")
          }
        }
      })
      console.log(gestureNames)
      res.status(200).send(gestureNames)
    }
  })
})

module.exports = router;
