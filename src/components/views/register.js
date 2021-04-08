import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'

import "../../styles/register.css"

async function handleSubmit(faceFile, lockFiles, unlockFiles) {
    console.log("DEBUG")
    console.log(`face file = ${JSON.stringify(faceFile)}`)
    console.log(`lock files = ${JSON.stringify(lockFiles)}`)
    console.log(`unlock files = ${JSON.stringify(unlockFiles)}`)
    // return fetch(`http://localhost:3001/faceUpload`, {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify(faceFile)
    // })
    //     .then(data => data.json())
}

export default function RegisterComponent() {
    const [faceFile, setFaceFile] = useState("Upload Face File")
    const [lockFiles, setLockFiles] = useState("Upload Lock Files")
    const [unlockFiles, setUnlockFiles] = useState("Upload Unlock Files")

    return (
        <div className="register-wrapper">
            <h2 id="register_header">Please enter your chosen face, lock and unlock combinations below to create an account</h2>
            <div className="user-forms">
                <Form>
                    <Form.Group>
                        <Form.File
                            id="face_file"
                            label={faceFile}
                            onChange={(e) => setFaceFile(e.target.file)}
                            type="file"
                        >
                            <Form.File.Label>Please select your face to authenticate with</Form.File.Label>
                            <Form.File.Input />
                        </Form.File>
                    </Form.Group>
                    <Form.Group>
                        <Form.File
                            id="lock_gesture_files"
                            label={JSON.stringify(lockFiles)}
                            onChange={(e) => setLockFiles(e.target.files)}
                            type="file"
                        >
                            <Form.File.Label>Chose gestures as your lock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                    <Form.Group>
                        <Form.File
                            id="unlock_gesture_files"
                            label={JSON.stringify(unlockFiles)}
                            onChange={(e) => setUnlockFiles(e.target.files)}
                            type="file"
                        >
                            <Form.File.Label>Chose gestures as your unlock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                    <Button
                        type="submit"
                        onSubmit={(e) => handleSubmit(faceFile, lockFiles, unlockFiles)}
                    >
                        Create Account
                    </Button>
                </Form>
            </div>
        </div>
    )
}