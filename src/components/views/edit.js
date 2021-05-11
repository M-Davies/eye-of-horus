import React, { useState } from 'react'
import axios from 'axios'
import Form from 'react-bootstrap/Form'
import ListGroup from 'react-bootstrap/ListGroup'
import Button from 'react-bootstrap/Button'
import Spinner from 'react-bootstrap/Spinner'
import PropTypes from 'prop-types'
import Webcam from 'react-webcam'

import { uploadFiles, uploadEncoded, checkCombination } from '../middleware'

export default function EditComponent({ username, authenticated }) {
    const [loading, setLoading] = useState(false)
    const [streaming, setStreaming] = useState(false)
    const [editFace, setEditFace] = useState(false)
    const [lockFiles, setLockFiles] = useState({})
    const [deleteLockFiles, setDeleteLockFiles] = useState()
    const [unlockFiles, setUnlockFiles] = useState({})
    const [lockDisplay, setLockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="lock-placeholder">Lock gesture combination unchanged</ListGroup.Item>
    ])
    const [showLockDisplay, setShowLockDisplay] = useState(false)
    const [unlockDisplay, setUnlockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="unlock-placeholder">Unlock gesture combination unchanged</ListGroup.Item>
    ])
    const [showUnlockDisplay, setShowUnlockDisplay] = useState(false)
    const webcamRef = React.useRef(null)

    async function editUser() {
        let lockNoFiles = null
        let unlockNoFiles = null
        try {
            lockNoFiles = Object.keys(lockFiles).length <= 0
        } catch (err) {
            lockNoFiles = true
        }
        try {
            unlockNoFiles = Object.keys(unlockFiles).length <= 0
        } catch (err) {
            unlockNoFiles = true
        }

        if (editFace === false && deleteLockFiles === false && lockNoFiles === true && unlockNoFiles === true) {
            return "Nothing selected to edit!"
        }

        let params = new FormData()
        params.append("user", username)

        if (editFace === true) {
            if (streaming === false) {
                return "Please enable video permissions in order to take a picture of your face"
            } else {
                // Get & upload face picture if streaming
                const facePath = await uploadEncoded(webcamRef.current.getScreenshot())
                if (!facePath instanceof Array) { return "Failed to upload screenshot from webcam" }
                params.append("face", facePath)
            }
        }

        // User can either delete their combination OR alter it OR leave it as unchanged
        if (deleteLockFiles === true) {
            params.append("delete", true)
        } else if (lockNoFiles === false) {
            let lockPaths = await uploadFiles(Array.from(lockFiles))
            const identifiedGestures = await checkCombination(lockPaths)
            if (identifiedGestures instanceof Array) {
                if (identifiedGestures.includes("UNKNOWN")) {
                    return `One or more gestures haven't been identified as a known gesture type, please ensure your image clearly shows the gesture being performed\n${identifiedGestures.join(' ')}`
                } else {
                    if (!window.confirm(`Identified your lock gesture combination as the below\nIs this correct?\n${identifiedGestures.join(' ')}`)) {
                        return "Please chose images for your gesture combination that clearly show the gesture type you wish to use"
                    }
                }
            } else {
                return "Failed to query server on gestures given, please try again later"
            }
            params.append("locks", lockPaths)
        }

        if (unlockNoFiles === false) {
            let unlockPaths = await uploadFiles(Array.from(unlockFiles))
            const identifiedGestures = await checkCombination(unlockPaths)
            if (identifiedGestures instanceof Array) {
                if (identifiedGestures.includes("UNKNOWN")) {
                    return `One or more gestures haven't been identified as a known gesture type, please ensure your image clearly shows the gesture being performed\n${identifiedGestures.join(' ')}`
                } else {
                    if (!window.confirm(`Identified your unlock gesture combination as the below\nIs this correct?\n${identifiedGestures.join(' ')}`)) {
                        return "Please chose images for your gesture combination that clearly show the gesture type you wish to use"
                    }
                }
            } else {
                return "Failed to query server on gestures given, please try again later"
            }
            params.append("unlocks", unlockPaths)
        }

        return axios.post("http://localhost:3001/user/edit", params)
            .then(res => {
                if (res.status === 201) {
                    return true
                } else {
                    return JSON.stringify(res.data)
                }
            })
            .catch(function (error) {
                try {
                    return error.response.data
                } catch {
                    return "Server error in editing user, please try again later"
                }
            })
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
                    Editing...
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

    function getLockInputs() {
        if (deleteLockFiles) {
            return (
                <fieldset disabled>
                    <Form.Group onChange={(e) => handleLockChange(e.target.files)}>
                        <Form.File
                            id="lock_gesture_form"
                            type="file"
                        >
                            <Form.File.Label>Lock Gesture Combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                        <Form.Check
                            type="checkbox"
                            label="Show Lock Combination"
                            defaultChecked={false}
                            onChange={() => setShowLockDisplay(!showLockDisplay)}
                        />
                    </Form.Group>
                </fieldset>
            )
        } else {
            return (
                <Form.Group onChange={(e) => handleLockChange(e.target.files)}>
                    <Form.File
                        id="lock_gesture_form"
                        type="file"
                    >
                        <Form.File.Label>Lock Gesture Combination</Form.File.Label>
                        <Form.File.Input multiple/>
                    </Form.File>
                    <Form.Check
                        type="checkbox"
                        label="Show Lock Combination"
                        defaultChecked={showLockDisplay}
                        onChange={() => setShowLockDisplay(!showLockDisplay)}
                    />
                </Form.Group>
            )
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

    const handleSubmit = async e => {
        e.preventDefault()

        setLoading(true)
        const editRes = await editUser()
        setLoading(false)

        // If successful at creating user, move to login
        if (editRes === true) {
            window.location.href = "/dashboard"
        } else {
            // If unsuccessful, return to default registration with error alert
            if (editRes.TYPE === undefined) {
                alert(`${editRes}`)
            } else {
                alert(`${editRes.TYPE}\n${editRes.MESSAGE}`)
            }
            window.location.href = "/edit"
        }
    }

    if (!authenticated) {
        window.location.href = "/"
    } else {
        if (navigator.mediaDevices.getUserMedia !== null && editFace === true) {
            navigator.getUserMedia({video:true},
                function (stream) {
                    setStreaming(true)
                },
                function (e) {
                    setStreaming(false)
                    if (e.name === "NotAllowedError") {
                        document.getElementById("video_display").hidden = true
                    }
                }
            )
        }

        return (
            <div className="edit-wrapper">
                <h1 id="edit_header">Add new values for features you would like to edit</h1>
                <Button block id="back_button" variant="info" href="/dashboard" disabled={loading}>Back</Button>
                { editFace === true &&
                    <Webcam
                        id="video_display"
                        audio={false}
                        screenshotFormat="image/jpeg"
                        ref={webcamRef}
                    />
                }
                <Form onSubmit={handleSubmit}>
                    <b hidden={editFace}>Enable Edit Face to change your stored face to the face in the webcam</b>
                    <Form.Group controlId="formBasicCheckbox">
                        <Form.Check
                            type="checkbox"
                            label="Edit Face"
                            defaultChecked={editFace}
                            onChange={() => setEditFace(!editFace)}
                        />
                    </Form.Group>
                    <Form.Check
                            type="checkbox"
                            label="Delete Lock Combination"
                            defaultChecked={false}
                            onChange={() => setDeleteLockFiles(!deleteLockFiles)}
                    />
                    {getLockInputs()}
                    <Form.Group onChange={(e) => handleUnlockChange(e.target.files)}>
                        <Form.File
                            id="unlock_gesture_form"
                            type="file"
                        >
                            <Form.File.Label>Unlock Gesture Combination</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                        <Form.Check
                            type="checkbox"
                            label="Show Unlock Combination"
                            defaultChecked={showUnlockDisplay}
                            onChange={() => setShowUnlockDisplay(!showUnlockDisplay)}
                        />
                    </Form.Group>
                    {getButton()}
                </Form>
                <ListGroup className="lock-display" hidden={!showLockDisplay}>
                    {lockDisplay}
                </ListGroup>
                <ListGroup className="unlock-display" hidden={!showUnlockDisplay}>
                    {unlockDisplay}
                </ListGroup>
            </div>
        )
    }
}

EditComponent.propTypes = {
    username: PropTypes.string,
    authenticated: PropTypes.bool
}
