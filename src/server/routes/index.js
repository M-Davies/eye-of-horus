var express = require('express')
var router = express.Router()
var fileUpload = require('express-fileupload')
var fs = require("fs")

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
          console.log("ERROR HAPPENED")
          console.log(err)
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
  const path = `${process.env.ROOT_DIR}/src/server/public/tempFile.jpg`

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
      console.log("ERROR HAPPENED")
      console.log(err)
      return res.status(500).send(err)
    }
  })

  console.log(`SUCCESSFULLY UPLOADED AND CONVERTED CAPTURE TO ${path}`)
  res.status(200).send([path])
})

module.exports = router;
