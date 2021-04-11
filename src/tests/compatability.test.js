/* eslint-disable no-undef */
/*
--------------------------------------------------------------------
Ensures the website can execute and parse the python script data

Copyright (c) 2021 Morgan Davies, UK
Released under GNU GPL v3 License
--------------------------------------------------------------------
*/

var spawn = require('child_process').spawn;
var fs = require('fs');

test('manager produces capturable debug', () => {
    var logs = null
    var response = null

    // Spawn child process calling manager script, this will fail but that does not matter
    const python = spawn("python", [
        `${process.env.ROOT_DIR}/src/scripts/manager.py`,
        "-a", "edit",
        "-p", "testuser",
        "-f", "fake.jpg"
    ]);

    // collect data from script
    python.stderr.on('data', function (data) {
        logs += "\n" + data.tostring()
    });

    // in close event we are sure that stream from child process is closed
    python.on('close', (code) => {
        console.log(`child process close all stdio with code ${code}`);
        response = fs.readFileSync("response.json", "utf-8")
    });

    expect(logs).not.toBeNull();
    expect(response).toBeInstanceOf(Object)
});
