var express = require("express");
var router = express.Router();
var cors = require('cors');

router.use(cors())

router.post("/", function(req, res, next) {
    res.send({
        token: "test123"
    });
});

module.exports = router;
