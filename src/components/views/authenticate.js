import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import Spinner from 'react-bootstrap/Spinner'
import ListGroup from 'react-bootstrap/ListGroup'
import PropTypes from 'prop-types'
import Webcam from 'react-webcam'
import axios from 'axios'

import { uploadFiles, uploadEncoded } from '../middleware'

import "../../styles/authenticate.css"

export default function AuthenticateComponent({
    username,
    userExists,
    setUserExists,
    authenticated,
    setAuthenticated,
    registering
}) {
    const [loading, setLoading] = useState(false)
    const [streaming, setStreaming] = useState(false)
    const [lockFiles, setLockFiles] = useState()
    const [unlockFiles, setUnlockFiles] = useState()
    const [lockDisplay, setLockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="lock-placeholder">No lock gestures added</ListGroup.Item>
    ])
    const [showLockDisplay, setShowLockDisplay] = useState(false)
    const [unlockDisplay, setUnlockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="unlock-placeholder">No unlock gestures added</ListGroup.Item>
    ])
    const [showUnlockDisplay, setShowUnlockDisplay] = useState(false)
    const webcamRef = React.useRef(null)

    async function createUser() {
        // Upload files (returning the error if something failed)
        let params = new FormData()
        params.append("user", username)
        if (streaming === false) {
            return "Please enable video permissions in order to take a picture of your face"
        } else {
            // Get & upload face picture if streaming
            const facePath = await uploadEncoded(webcamRef.current.getScreenshot())
            if (!facePath instanceof Array) { return "Failed to upload screenshot from webcam" }
            params.append("face", facePath)
        }

        if (lockFiles === undefined || lockFiles === null) { return "No lock files were selected" }
        const lockPaths = await uploadFiles(Array.from(lockFiles))
        if (!lockPaths instanceof Array) { return "Failed to upload lock files" }
        params.append("locks", lockPaths)

        if (unlockFiles === undefined || unlockFiles === null) { return "No unlock files were selected" }
        const unlockPaths = await uploadFiles(Array.from(unlockFiles))
        if (!unlockPaths instanceof Array) { return "Failed to upload unlock files" }
        params.append("unlocks", unlockPaths)

        console.log("Requesting user create with params")
        console.log(params.username)
        console.log(params.face)
        console.log(params.locks)
        console.log(params.unlocks)

        // Create user profile
        return axios.post("http://localhost:3001/user/create", params)
            .then(res => {
                if (res.status === 201) {
                    return true
                } else {
                    return JSON.stringify(res.data)
                }
            })
            .catch(function (error) {
                if (error.response.data) {
                    return error.response.data
                } else {
                    throw new Error(error.toString())
                }
            })
    }

    async function loginUser() {
        // Upload files (returning the error if something failed)
        let params = new FormData()
        params.append("user", username)
        if (streaming === false) {
            return "Please enable video permissions in order to take a picture of your face"
        } else {
            // Get & upload face picture if streaming
            const facePath = await uploadEncoded(webcamRef.current.getScreenshot())
            if (!facePath instanceof Array) { return "Failed to upload screenshot from webcam" }
            params.append("face", facePath)
        }

        if (unlockFiles === undefined || unlockFiles === null) { return "No unlock files were selected" }
        const unlockPaths = await uploadFiles(Array.from(unlockFiles))
        if (!unlockPaths instanceof Array) { return "Failed to upload unlock files" }
        params.append("unlocks", unlockPaths)

        // Authenticate user
        return axios.post("http://localhost:3001/user/auth", params)
            .then(res => {
                if (res.status === 200) {
                    return true
                } else {
                    return JSON.stringify(res.data)
                }
            })
            .catch(function (error) {
                if (error.response.data) {
                    return error.response.data
                } else {
                    throw new Error(error.toString())
                }
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
        setLoading(true)

        if (registering) {
            // Send create request to server
            const userCreateRes = await createUser()
            setLoading(false)

            // If successful at creating user, move to login
            if (userCreateRes === true) {
                setUserExists(userCreateRes)
                setAuthenticated(true)
                window.location.href = "/dashboard"
            } else {
                // If unsuccessful, return to default registration with error alert
                if (userCreateRes.TYPE === undefined) {
                    alert(`${userCreateRes}`)
                } else {
                    alert(`${userCreateRes.TYPE}\n${userCreateRes.MESSAGE}`)
                }
                window.location.href = "/register"
            }
        } else {
            // Send login request to server
            const userLoginRes = await loginUser()
            setLoading(false)

            // If successful at logging in user, move to dashboard
            if (userLoginRes === true) {
                setAuthenticated(true)
                window.location.href = "/dashboard"
            } else if (userLoginRes.CODE === 10) {
                setAuthenticated(false)
                alert(`Failed to login with given face or unlock credentials\n${userLoginRes.MESSAGE}`)
                window.location.href = "/login"
            } else {
                // If unsuccessful, return to default login with error alert
                if (userLoginRes.TYPE === undefined) {
                    alert(`${userLoginRes}`)
                } else {
                    alert(`${userLoginRes.TYPE}\n${userLoginRes.MESSAGE}`)
                }
                window.location.href = "/login"
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
                <h2 id="authenticate_header">Hello {username}! Please stream a face and upload your lock and unlock combinations to create an account</h2>
            )
        } else {
            return (
                <h2 id="authenticate_header">Welcome back {username}. Please stream your face and upload your unlock combination</h2>
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
                        <Form.Check
                            type="checkbox"
                            label="Show Lock Combination"
                            defaultChecked={showLockDisplay}
                            onChange={() => setShowLockDisplay(!showLockDisplay)}
                        />
                    </Form.Group>
                    <Form.Group onChange={(e) => handleUnlockChange(e.target.files)}>
                        <Form.File
                            id="unlock_gesture_form"
                            type="file"
                        >
                            <Form.File.Label>Chose at least 4 other gestures as your unlock gesture combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                        <Form.Check
                            type="checkbox"
                            label="Show Unlock Combination"
                            defaultChecked={showUnlockDisplay}
                            onChange={() => setShowUnlockDisplay(!showUnlockDisplay)}
                        />
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
                                <Form.File.Label>No lock gesture combination needed for logging in</Form.File.Label>
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
                        <Form.Check
                            type="checkbox"
                            label="Show Unlock Combination"
                            defaultChecked={showUnlockDisplay}
                            onChange={() => setShowUnlockDisplay(!showUnlockDisplay)}
                        />
                    </Form.Group>
                    <Button variant="danger" href="/forgot">Forgotten Unlock Combination</Button>
                </div>
            )
        }
    }

    function getButton() {
        if (loading) {
            return (
                <Button variant="success" type="submit" disabled>
                    <Spinner
                        as="span"
                        animation="grow"
                        role="status"
                        aria-hidden="true"
                    />
                    Loading...
                </Button>
            )
        } else {
            return (
                <Button variant="primary" type="submit">
                    Submit
                </Button>
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
        if (navigator.mediaDevices.getUserMedia !== null) {
            navigator.getUserMedia({video:true},
                function (stream) {
                    setStreaming(true)
                },
                function (e) {
                    setStreaming(false)
                    if (e.name === "NotAllowedError") {
                        console.log("Video perms denied")
                        document.getElementById("video_display").hidden = true
                    } else {
                        console.log("background error : " + e.name)
                    }
                }
            )
        }

        return (
            <div className="authenticate-wrapper">
                {getHeader()}
                <div className="user-forms">
                    <Button block id="back_button" variant="info" href="/" disabled={loading}>Back</Button>
                    <Webcam id="video_display" audio={false} screenshotFormat="image/jpeg" ref={webcamRef} />
                    <Form onSubmit={handleSubmit}>
                        {getGestureForms()}
                        {getButton()}
                    </Form>
                    <ListGroup className="lock-display" hidden={!showLockDisplay}>
                        {lockDisplay}
                    </ListGroup>
                    <ListGroup className="unlock-display" hidden={!showUnlockDisplay}>
                        {unlockDisplay}
                    </ListGroup>
                </div>
            </div>
        )
    }
}

AuthenticateComponent.propTypes = {
    username: PropTypes.string,
    userExists: PropTypes.bool,
    setUserExists: PropTypes.func,
    authenticated: PropTypes.bool,
    setAuthenticated: PropTypes.func,
    registering: PropTypes.bool.isRequired
}
