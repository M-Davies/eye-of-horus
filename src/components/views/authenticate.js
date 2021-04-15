import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import ListGroup from 'react-bootstrap/ListGroup'
import PropTypes from 'prop-types'
import axios from 'axios'

import "../../styles/authenticate.css"

export default function AuthenticateComponent({
    username,
    userExists,
    setUserExists,
    authenticated,
    setAuthenticated,
    registering
}) {
    const [faceFile, setFaceFile] = useState()
    const [lockFiles, setLockFiles] = useState()
    const [unlockFiles, setUnlockFiles] = useState()
    const [lockDisplay, setLockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="lock-placeholder">No lock gestures added</ListGroup.Item>
    ])
    const [unlockDisplay, setUnlockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="unlock-placeholder">No unlock gestures added</ListGroup.Item>
    ])

    async function uploadFiles(files) {
        let params = new FormData()

        // Uploading 1 or more files?
        if (Array.isArray(files)) {
            let count = 1
            files.forEach(file => {
                params.append(`file_${count}`, file)
                count++
            })
        } else {
            params.append(`file`, files)
        }

        // Upload and return paths
        return axios.post(`http://localhost:3001/upload`, params)
            .then(res => {
                console.log(res)
                return Array.from(res.data)
            })
            .catch((error) => {
                throw new Error(error.toString())
            })
    }

    async function createUser() {
        console.log("DEBUG")
        console.log(`username`)
        console.log(username)
        console.log(`face file`)
        console.log(faceFile)
        console.log(`lock files`)
        console.log(lockFiles)
        console.log(`unlock files`)
        console.log(unlockFiles)

        // Upload files
        let facePath = await uploadFiles(faceFile)
        let lockPaths = await uploadFiles(Array.from(lockFiles))
        let unlockPaths = await uploadFiles(Array.from(unlockFiles))
        console.log(facePath)

        // Create user profile
        let params = new FormData()
        params.append("user", username)
        params.append("face", facePath)
        params.append("locks", lockPaths)
        params.append("unlocks", unlockPaths)

        return axios.post(`http://localhost:3001/user/create`, params)
            .then(res => {
                console.log(res)
                if (res.status === 201) {
                    return true
                } else {
                    return JSON.stringify(res.data)
                }
            })
            .catch((error) => {
                throw new Error(error.toString())
            })
    }

    async function loginUser() {
        console.log("DEBUG")
        console.log(`username`)
        console.log(username)
        console.log(`face file`)
        console.log(faceFile)
        console.log(`unlock files`)
        console.log(unlockFiles)

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
            // On success return bool, otherwise return the response from server
            if (data === 200) {
                return true
            } else {
                return data
            }
        })
        .catch((error) => {
            throw new Error(error.toString())
        })
    }

    const handleLockChange = (files) => {
        setLockFiles(files)
        generateFileList(files, null)
    }

    const handleUnlockChange = (files) => {
        setUnlockFiles(files)
        generateFileList(null, files)
    }

    const handleSubmit = async e => {
        e.preventDefault()

        if (registering) {
            // Send create request to server
            const userCreateRes = await createUser()

            // If successfull at creating user, move to login
            if (userCreateRes === true) {
                setUserExists(userCreateRes)
                window.location.href = "/login"
            } else {
                // If unsuccessful, return to default registration with error alert
                window.location.href = "/register"
                alert(`${userCreateRes.messageType}\n\n${userCreateRes.message}`)
            }
        } else {
            // Send login request to server
            const userLoginRes = await loginUser()

            // If successful at logging in user, move to dashboard
            if (userLoginRes === true) {
                setAuthenticated(true)
                window.location.href = "/dashboard"
            } else {
                // If unsuccessful, return to default login with error alert
                window.location.href = "/login"
                alert(`${userLoginRes.messageType}\n\n${userLoginRes.message}`)
            }
        }
    }

    function generateFileList(lock=null, unlock=null) {
        // Whenever files are selected by the user, update the list group to display the loaded items in order
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

    function getHeader() {
        // Header changes depending on whether we are registering or logging in
        if (registering) {
            return (
                <h2 id="register_header">Hello {username}! Looks like this is your first time, so please enter your chosen face, lock and unlock combinations below to create an account</h2>
            )
        } else {
            return (
                <h2 id="login_header">Welcome back {username}. Please enter your chosen face, lock and unlock combinations below to authenticate yourself</h2>
            )
        }
    }

    function getGestureForms() {
        if (registering) {
            // If this is a registration page, generate the editable forms depending on the given
            return (
                <div className="gesture-forms">
                    <Form.Group onChange={(e) => handleLockChange(e.target.files)}>
                        <Form.File
                            id="lock_gesture_form"
                            type="file"
                        >
                            <Form.File.Label>Chose at least 4 gestures as your lock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                    <Form.Group onChange={(e) => handleUnlockChange(e.target.files)}>
                        <Form.File
                            id="unlock_gesture_form"
                            type="file"
                        >
                            <Form.File.Label>Chose another 4 gestures at least as your unlock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                </div>
            )
        } else {
            // If this is a login page, generate the lock form in a disabled state
            return (
                <div className="gesture-forms">
                    <fieldset disabled>
                        <Form.Group onChange={(e) => handleLockChange(e.target.files)}>
                            <Form.File
                                id="lock_gesture_form"
                                type="file"
                            >
                                <Form.File.Label>You are logging in so no need for a lock gesture combination</Form.File.Label>
                                <Form.File.Input multiple/>
                            </Form.File>
                        </Form.Group>
                    </fieldset>
                    <Form.Group onChange={(e) => handleUnlockChange(e.target.files)}>
                        <Form.File
                            id="unlock_gesture_form"
                            type="file"
                        >
                            <Form.File.Label>Please enter your unlock combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                    </Form.Group>
                </div>
            )
        }
    }

    if (authenticated === true) {
        window.location.href = "/dashboard"
    } else if (userExists === true && window.location.pathname === "/register") {
        window.location.href = "/login"
    } else if (userExists === false && window.location.pathname === "/login") {
        window.location.href = "/register"
    } else {
        return (
            <div className="authenticate-wrapper">
                {getHeader()}
                <div className="user-forms">
                    <Form onSubmit={handleSubmit}>
                        <Form.Group onChange={(e) => setFaceFile(e.target.files[0])}>
                            <Form.File
                                id="face_file_form"
                                type="file"
                            >
                                <Form.File.Label>Please select a face to authenticate with</Form.File.Label>
                                <Form.File.Input />
                            </Form.File>
                        </Form.Group>
                        {getGestureForms()}
                        <Button
                            type="submit"
                        >
                            Submit
                        </Button>
                    </Form>
                    <ListGroup className="lock-display">
                        {lockDisplay}
                    </ListGroup>
                    <ListGroup className="unlock-display">
                        {unlockDisplay}
                    </ListGroup>
                </div>
            </div>
        )
    }
}

AuthenticateComponent.propTypes = {
    username: PropTypes.string,
    setUserExists: PropTypes.func,
    setAuthenticated: PropTypes.func,
    registering: PropTypes.bool
}
