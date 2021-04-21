import React, { useState } from 'react'
import Form from 'react-bootstrap/Form'
import Button from 'react-bootstrap/Button'
import ListGroup from 'react-bootstrap/ListGroup'
import Spinner from 'react-bootstrap/Spinner'
import PropTypes from 'prop-types'
import axios from 'axios'
import Webcam from 'react-webcam'

import { uploadFiles, uploadEncoded } from '../middleware'

import '../../styles/forgot.css'

export default function ForgotComponent({username, authenticated, setAuthenticated}) {
    const [files, setFiles] = useState()
    const [loading, setLoading] = useState(false)
    const [streaming, setStreaming] = useState(false)
    const [forgotBoth, setForgotBoth] = useState(false)
    const [display, setDisplay] = useState([
        <ListGroup.Item variant="secondary" key="unlock-placeholder">No Lock gestures added</ListGroup.Item>
    ])
    const [showDisplay, setShowGestureDisplay] = useState(false)
    const webcamRef = React.useRef(null)

    const handleGestureChange = (files) => {
        if (files !== null) {
            setFiles(files)
            let currentLockDisplay = []
            let lockCount = 1
            Array.from(files).forEach(file => {
                let key = `lock-placeholder-${lockCount}`
                currentLockDisplay.push(<ListGroup.Item key={key}>Lock Gesture {lockCount} = {file.name}</ListGroup.Item>)
                lockCount++
            })
            setDisplay(currentLockDisplay)
        }
    }

    async function checkFaceMatch() {
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

        return axios.post("http://localhost:3001/user/face", params)
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
                    return "Server error in checking user face, please try again later"
                }
            })
    }

    const handleSubmit = async e => {
        e.preventDefault()
        setLoading(true)
        if (forgotBoth === true) {
            const checkFace = await checkFaceMatch()
            setLoading(false)

            if (checkFace === true) {
                setAuthenticated(true)
                alert("Face matches, you are now logged in and can change your gesture combinations")
                window.location.href = "/edit"
            } else {
                if (checkFace.TYPE === undefined) {
                    alert(`${checkFace}`)
                } else {
                    alert(`${checkFace.TYPE}\n${checkFace.MESSAGE}`)
                }
                window.location.href = "/forgot"
            }
        } else {
            const checkRes = await checkCombination()
            setLoading(false)

            if (checkRes === true) {
                setAuthenticated(true)
                alert("Lock combination is correct, you are now signed in and can change your unlock combination")
                window.location.href = "/edit"
            } else {
                if (checkRes.TYPE === undefined) {
                    alert(`${checkRes}`)
                } else {
                    alert(`${checkRes.TYPE}\n${checkRes.MESSAGE}`)
                }
                window.location.href = "/forgot"
            }
        }
    }

    const handleForgotBoth = async e => {
        setForgotBoth(true)
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
    }

    async function checkCombination() {
        let params = new FormData()
        params.append("user", username)
        if (files === undefined) { return "No lock files were selected" }
        const paths = await uploadFiles(Array.from(files))
        if (!paths instanceof Array) { return "Failed to upload lock files" }
        params.append("locks", paths)

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
                    return "Server error in authenticating user, please try again later"
                }
            })
    }

    function getButton() {
        if (loading) {
            return (
                <Button variant="success" type="submit" disabled id="submit_button">
                    <Spinner
                        as="span"
                        animation="grow"
                        role="status"
                        aria-hidden="true"
                    />
                    Checking Lock combination...
                </Button>
            )
        } else {
            return (
                <Button variant="primary" type="submit" id="submit_button">
                    Submit
                </Button>
            )
        }
    }

    function getGestureForm() {
        if (forgotBoth) {
            return (
                <fieldset disabled>
                    <Form.Group onChange={(e) => handleGestureChange(e.target.files)}>
                        <Form.File
                            id="gesture_form"
                            type="file"
                        >
                            <Form.File.Label>Recovering your lock and unlock combinations using your face...</Form.File.Label>
                            <Form.File.Input multiple/>
                        </Form.File>
                        <Form.Check
                            type="checkbox"
                            label="Show Lock Combination"
                            defaultChecked={showDisplay}
                            onChange={() => setShowGestureDisplay(!showDisplay)}
                        />
                    </Form.Group>
                </fieldset>
            )
        } else {
            return (
                <Form.Group onChange={(e) => handleGestureChange(e.target.files)}>
                    <Form.File
                        id="gesture_form"
                        type="file"
                    >
                        <Form.File.Label>Enter your Lock combination</Form.File.Label>
                        <Form.File.Input multiple/>
                    </Form.File>
                    <Form.Check
                        type="checkbox"
                        label="Show Lock Combination"
                        defaultChecked={showDisplay}
                        onChange={() => setShowGestureDisplay(!showDisplay)}
                    />
                </Form.Group>
            )
        }
    }

    function getWebcam() {
        if (forgotBoth) { return (<Webcam id="video_display" audio={false} screenshotFormat="image/jpeg" ref={webcamRef} />) }
    }

    if (!username || authenticated) {
        window.location.href = "/"
    } else {
        return (
            <div className="forgot-wrapper">
                <h2 id="forgot_header">{forgotBoth === false ? "Please enter your Lock combination to recover your Unlock combination" : "Using your face to recover your lock and unlock combinations"}</h2>
                <Button block id="back_button" variant="info" href="/login" disabled={loading}>Back</Button>
                {getWebcam()}
                <Form onSubmit={handleSubmit}>
                    {getGestureForm()}
                    <Button
                        id="forgot_button"
                        variant="danger"
                        disabled={loading}
                        onClick={() => handleForgotBoth()}
                        hidden={forgotBoth}
                    >
                        Forgotten Lock combination
                    </Button>
                    {getButton()}
                </Form>
                <ListGroup className="display" hidden={!showDisplay}>
                    {display}
                </ListGroup>
            </div>
        )
    }
}

ForgotComponent.propTypes = {
    username: PropTypes.string.isRequired,
    authenticated: PropTypes.bool,
    setAuthenticated: PropTypes.func.isRequired
}
