var express = require('express')
var router = express.Router()
var fileUpload = require('express-fileupload')
var fs = require("fs")
var util = require("util")

router.use(fileUpload())

const unlink = util.promisify(fs.unlink)

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Express' })
})

router.post('/upload', function(req, res, next) {
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

module.exports = router;
