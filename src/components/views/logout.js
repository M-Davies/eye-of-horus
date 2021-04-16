import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import Spinner from 'react-bootstrap/Spinner'
import ListGroup from 'react-bootstrap/ListGroup'
import PropTypes from 'prop-types'
import axios from 'axios'

import { ClearTokens } from '../token'
import { uploadFiles } from '../middleware'

export default function LogoutComponent({ username, authenticated, setAuthenticated }) {
    const [loading, setLoading] = useState(false)
    const [faceFile, setFaceFile] = useState()
    const [lockFiles, setLockFiles] = useState()
    const [lockDisplay, setLockDisplay] = useState([
        <ListGroup.Item variant="secondary" key="unlock-placeholder">No unlock gestures added</ListGroup.Item>
    ])

    const handleLockChange = (files) => {
        setLockFiles(files)
        let currentLockDisplay = []
        let lockCount = 1
        Array.from(files).forEach(file => {
            let key = `lock-placeholder-${lockCount}`
            currentLockDisplay.push(<ListGroup.Item key={key}>Lock Gesture {lockCount} = {file.name}</ListGroup.Item>)
            lockCount++
        })
        setLockDisplay(currentLockDisplay)
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
                    Logging out...
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

    async function logoutUser() {
        if (!faceFile ) { return "No face file was selected" }
        if (!lockFiles ) { return "No lock files were selected" }
        let facePath = await uploadFiles(faceFile)
        let lockPaths = await uploadFiles(Array.from(lockFiles))
        let params = new FormData()
        params.append("user", username)
        params.append("face", facePath)
        params.append("locks", lockPaths)
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

    const handleSubmit = async e => {
        e.preventDefault()
        setLoading(true)
        const userLogoutRes = await logoutUser()
        setLoading(false)

        // If successful at creating user, move to login
        if (userLogoutRes === true) {
            ClearTokens()
            window.location.href = "/"
        } else {
            // If unsuccessful, return to default registration with error alert
            if (userLogoutRes.TYPE === undefined) {
                alert(`${userLogoutRes}`)
            } else {
                alert(`${userLogoutRes.TYPE}\n${userLogoutRes.MESSAGE}`)
            }
            window.location.href = "/logout"
        }
    }

    if (authenticated === false) {
        window.location.href = "/"
    } else {
        return (
            <div className="logout-wrapper">
                <Button variant="secondary" href="/dashboard">Back</Button>
                <h1>Select your face file and lock combination to log out</h1>
                <div className="user-forms">
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
                        <Form.Group onChange={(e) => handleLockChange(e.target.files)}>
                            <Form.File
                                id="lock_gesture_form"
                                type="file"
                            >
                                <Form.File.Label>Lock Combination</Form.File.Label>
                                <Form.File.Input multiple/>
                            </Form.File>
                        </Form.Group>
                        <fieldset disabled>
                            <Form.Group>
                                <Form.File
                                    id="unlock_gesture_form"
                                    type="file"
                                >
                                    <Form.File.Label>You are logging out so no need for a unlock gesture combination</Form.File.Label>
                                    <Form.File.Input multiple/>
                                </Form.File>
                            </Form.Group>
                        </fieldset>
                        {getButton()}
                    </Form>
                    <ListGroup className="lock-display">
                        {lockDisplay}
                    </ListGroup>
                </div>
            </div>
        )
    }
}

LogoutComponent.propTypes = {
    username: PropTypes.string,
    authenticated: PropTypes.bool,
    setAuthenticated: PropTypes.func
}
