import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import Spinner from 'react-bootstrap/Spinner'
import ListGroup from 'react-bootstrap/ListGroup'
import PropTypes from 'prop-types'
import axios from 'axios'

import { uploadFiles } from '../middleware'

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
    const [faceFile, setFaceFile] = useState()
    const [lockFiles, setLockFiles] = useState()
    const [unlockFiles, setUnlockFiles] = useState()
    const [lockDisplay, setLockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="lock-placeholder">No lock gestures added</ListGroup.Item>
    ])
    const [unlockDisplay, setUnlockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="unlock-placeholder">No unlock gestures added</ListGroup.Item>
    ])

    async function createUser() {
        // Upload files (returning the error if something failed)
        if (!faceFile ) { return "No face file was selected" }
        if (!lockFiles ) { return "No lock files were selected" }
        if (!unlockFiles) { return "No unlock files were selected" }
        let facePath = await uploadFiles(faceFile)
        let lockPaths = await uploadFiles(Array.from(lockFiles))
        let unlockPaths = await uploadFiles(Array.from(unlockFiles))

        // Create user profile
        let params = new FormData()
        params.append("user", username)
        params.append("face", facePath)
        params.append("locks", lockPaths)
        params.append("unlocks", unlockPaths)

        return axios.post("http://localhost:3001/user/create", params)
            .then(res => {
                setLoading(false)
                if (res.status === 201) {
                    return true
                } else {
                    return JSON.stringify(res.data)
                }
            })
            .catch(function (error) {
                setLoading(false)
                if (error.response.data) {
                    return error.response.data
                } else {
                    throw new Error(error.toString())
                }
            })
    }

    async function loginUser() {
        // Upload files (returning the error if something failed)
        if (!faceFile ) { return "No face file was selected" }
        if (!unlockFiles) { return "No unlock files were selected" }
        let facePath = await uploadFiles(faceFile)
        let unlockPaths = await uploadFiles(Array.from(unlockFiles))

        // Create user profile
        let params = new FormData()
        params.append("user", username)
        params.append("face", facePath)
        params.append("unlocks", unlockPaths)
        return axios.post("http://localhost:3001/user/auth", params)
            .then(res => {
                setLoading(false)
                if (res.status === 200) {
                    return true
                } else {
                    return JSON.stringify(res.data)
                }
            })
            .catch(function (error) {
                setLoading(false)
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

            // If successful at logging in user, move to dashboard
            if (userLoginRes === true) {
                setAuthenticated(true)
                window.location.href = "/dashboard"
            } else if (userLoginRes.CODE === 10) {
                setAuthenticated(false)
                alert("Failed to login with given face or unlock credentials")
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
                            <Form.File.Label>Chose at least 4 other gestures as your unlock gesture combination</Form.File.Label>
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
                    Working...
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
        return (
            <div className="authenticate-wrapper">
                {getHeader()}
                <div className="user-forms">
                    <Button variant="secondary" href="/" disabled={loading === true ? true : false}>Back</Button>
                    <Form onSubmit={handleSubmit}>
                        <Form.Group onChange={(e) => setFaceFile(e.target.files[0])}>
                            <Form.File
                                id="face_file_form"
                                type="file"
                            >
                                <Form.File.Label>Face File</Form.File.Label>
                                <Form.File.Input />
                            </Form.File>
                        </Form.Group>
                        {getGestureForms()}
                        {getButton()}
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
    userExists: PropTypes.bool,
    setUserExists: PropTypes.func,
    authenticated: PropTypes.bool,
    setAuthenticated: PropTypes.func,
    registering: PropTypes.bool.isRequired
}
