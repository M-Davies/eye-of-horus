import React, { useState } from 'react'
import axios from 'axios'
import Form from 'react-bootstrap/Form'
import ListGroup from 'react-bootstrap/ListGroup'
import Button from 'react-bootstrap/Button'
import Spinner from 'react-bootstrap/Spinner'
import PropTypes from 'prop-types'

import { uploadFiles } from '../middleware'

export default function EditComponent({ username, authenticated }) {
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
        if (!faceFile && lockNoFiles && unlockNoFiles) {
            return "Nothing selected to edit!"
        }

        let params = new FormData()
        params.append("user", username)

        if (faceFile) {
            let facePath = await uploadFiles(faceFile)
            params.append("face", facePath)
        }

        if (!lockNoFiles) {
            let lockPaths = await uploadFiles(Array.from(lockFiles))
            params.append("locks", lockPaths)
        }

        if (!unlockNoFiles) {
            let unlockPaths = await uploadFiles(Array.from(unlockFiles))
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
                if (error.response.data) {
                    return error.response.data
                } else {
                    throw new Error(error.toString())
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
        return (
            <div className="edit-wrapper">
                <h1>Please change which features you would like to edit</h1>
                <Button id="back_button" variant="secondary" href="/dashboard" disabled={loading === true ? true : false}>Back</Button>
                <Form onSubmit={handleSubmit}>
                        <Form.Group onChange={(e) => setFaceFile(e.target.files[0])}>
                            <Form.File
                                id="face_file_form"
                                type="file"
                            >
                                <Form.File.Label>Face</Form.File.Label>
                                <Form.File.Input />
                            </Form.File>
                        </Form.Group>
                        <Form.Group onChange={(e) => handleLockChange(e.target.files)}>
                            <Form.File
                                id="lock_gesture_form"
                                type="file"
                            >
                                <Form.File.Label>Chose at least 4 gestures as your new lock gesture combination</Form.File.Label>
                                <Form.File.Input multiple/>
                            </Form.File>
                        </Form.Group>
                        <Form.Group onChange={(e) => handleUnlockChange(e.target.files)}>
                            <Form.File
                                id="unlock_gesture_form"
                                type="file"
                            >
                                <Form.File.Label>Chose at least 4 other gestures as your new unlock gesture combination</Form.File.Label>
                                <Form.File.Input multiple/>
                            </Form.File>
                        </Form.Group>
                        {getButton()}
                </Form>
                <ListGroup className="lock-display">
                    {lockDisplay}
                </ListGroup>
                <ListGroup className="unlock-display">
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
