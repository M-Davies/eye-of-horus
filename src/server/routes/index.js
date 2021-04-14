var express = require('express')
var router = express.Router()
var fileUpload = require('express-fileupload')
var fs = require("fs")

router.use(fileUpload())

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Express' })
})

router.post('/upload', function(req, res, next) {
  console.log("FILES CONTENTS")
  console.log(req.files)

  // Iterate through files and upload one at a time
  let uploadedPaths = []
  Object.keys(req.files).forEach(fileWrapper => {
    let fileObj = req.files[fileWrapper]
    console.log(`UPLOADING ${fileObj}`)
    let currentFilePath = `${process.env.ROOT_DIR}/src/server/public/${fileObj.name}`

    // Delete old copy if it exists
    fs.unlink(currentFilePath, function(err) {
      if(err && err.code == 'ENOENT') {
        // File doens't exist
        console.info("Old File doesn't exist, won't remove it.")
      } else if (err) {
        // Other errors, e.g. maybe we don't have enough permission
        res.status(500).send("Error occurred while trying to remove file")
      } else {
        console.info("Successfully deleted old file");
      }
    })

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
