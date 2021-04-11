import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import ListGroup from 'react-bootstrap/ListGroup'
import PropTypes from 'prop-types'

import "../../styles/authenticate.css"

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
    const [lockDisplay, setLockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="lock-placeholder">No lock gestures added</ListGroup.Item>
    ])
    const [unlockDisplay, setUnlockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="unlock-placeholder">No unlock gestures added</ListGroup.Item>
    ])

    const handleSubmit = async e => {
        e.preventDefault()

        if (registering) {
            setUserExists(await createUser(username, faceFile, lockFiles, unlockFiles))
            window.location.href = "/login"
        } else {
            setAuthenticated(await loginUser(username, faceFile, unlockFiles))
            window.location.href = "/dashboard"
        }
    }

    async function generateFileList(lock=null, unlock=null) {
        if (lock !== null) {
            let currentLockDisplay = []
            let lockCount = 1
            Array.from(lock).forEach(file => {
                let key = `lock-placeholder-${lockCount}`
                currentLockDisplay.push(<ListGroup.Item key={key}>Lock Gesture {lockCount} = {file.name}</ListGroup.Item>)
                lockCount++
            })
            setLockDisplay(currentLockDisplay)
        }

        if (unlock !== null) {
            let currentUnlockDisplay = []
            let unlockCount = 1
            Array.from(unlock).forEach(file => {
                let key = `unlock-placeholder-${unlockCount}`
                currentUnlockDisplay.push(<ListGroup.Item key={key}>Unlock Gesture {unlockCount} = {file.name}</ListGroup.Item>)
                unlockCount++
            })
            setUnlockDisplay(currentUnlockDisplay)
        }
    }

    const handleLockChange = (files) => {
        setLockFiles(files)
        generateFileList(files, null)
    }

    const handleUnlockChange = (files) => {
        setUnlockFiles(files)
        generateFileList(null, files)
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
        <div className="authenticate-wrapper">
            {getHeader()}
            <div className="user-forms">
                <Form onSubmit={handleSubmit}>
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
                    <Form.Group onChange={(e) => handleLockChange(e.target.files)}>
                        <Form.File
                            id="lock_gesture_files"
                            label={JSON.stringify(lockFiles)}
                            type="file"
                        >
                            <Form.File.Label>Chose at least 4 gestures as your lock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                    <Form.Group onChange={(e) => handleUnlockChange(e.target.files)}>
                        <Form.File
                            id="unlock_gesture_files"
                            label={JSON.stringify(unlockFiles)}
                            type="file"
                        >
                            <Form.File.Label>Chose another 4 gestures at least as your unlock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                    <Button
                        type="submit"
                    >
                        Create Account
                    </Button>
                </Form>
                <ListGroup className="lock-group">
                    {lockDisplay}
                </ListGroup>
                <ListGroup className="unlock-group">
                    {unlockDisplay}
                </ListGroup>
            </div>
        </div>
    )
}

AuthenticateComponent.propTypes = {
    username: PropTypes.string,
    setUserExists: PropTypes.func,
    setAuthenticated: PropTypes.func,
    registering: PropTypes.bool
}
