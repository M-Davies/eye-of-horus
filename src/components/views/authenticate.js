import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import PropTypes from 'prop-types';

import "../../styles/register.css"

async function createUser(username, faceFile, lockFiles, unlockFiles) {
    console.log("DEBUG")
    console.log(`username = ${username}`)
    console.log(`face file = ${JSON.stringify(faceFile)}`)
    console.log(`lock files = ${JSON.stringify(lockFiles)}`)
    console.log(`unlock files = ${JSON.stringify(unlockFiles)}`)

    return fetch(`http://localhost:3001/user/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user : username,
            face : faceFile,
            lock : lockFiles,
            unlock : unlockFiles
        })
    })
    .then(data => data.json())
    .then(data => {
        if (data === true) {
            return true
        } else {
            return false
        }
    })
    .catch((error) => {
        console.error(error)
    })
}

async function loginUser(username, faceFile, unlockFiles) {
    console.log("DEBUG")
    console.log(`username = ${username}`)
    console.log(`face file = ${JSON.stringify(faceFile)}`)
    console.log(`unlock files = ${JSON.stringify(unlockFiles)}`)

    return fetch(`http://localhost:3001/user/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user : username,
            face : faceFile,
            unlock : unlockFiles
        })
    })
    .then(data => data.json())
    .then(data => {
        if (data === true) {
            return true
        } else {
            return false
        }
    })
    .catch((error) => {
        console.error(error)
    })
}

export default function AuthenticateComponent({ username, setUserExists, setAuthenticated, registering }) {
    const [faceFile, setFaceFile] = useState()
    const [lockFiles, setLockFiles] = useState()
    const [unlockFiles, setUnlockFiles] = useState()

    const handleSubmit = async e => {
        e.preventDefault()
        if (registering) {
            setUserExists(await createUser(username, faceFile, lockFiles, unlockFiles))
        } else {
            setAuthenticated(await loginUser(username, faceFile, unlockFiles))
        }
    }

    function getHeader() {
        if (registering) {
            return (
                <h2 id="register_header">Hello {username}! Looks like this is your first time here so please enter your chosen face, lock and unlock combinations below to create an account</h2>
            )
        } else {
            return (
                <h2 id="login_header">Welcome back {username}. Please enter your chosen face, lock and unlock combinations below to authenticate yourself</h2>
            )
        }
    }

    return (
        <div className="register-wrapper">
            {getHeader}
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
                            <Form.File.Label>Chose at least 4 gestures as your lock gesture combination</Form.File.Label>
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
                            <Form.File.Label>Chose another 4 gestures at least as your unlock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                    <Button
                        type="submit"
                        onSubmit={handleSubmit}
                    >
                        Create Account
                    </Button>
                </Form>
            </div>
        </div>
    )
}

AuthenticateComponent.propTypes = {
    username: PropTypes.string.isRequired,
    setUserExists: PropTypes.func.isRequired,
    setAuthenticated: PropTypes.func.isRequired,
    registering: PropTypes.bool.isRequired
}
