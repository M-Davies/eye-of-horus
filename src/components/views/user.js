import React, { useState } from 'react'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Spinner from 'react-bootstrap/Spinner'
import PropTypes from 'prop-types'

import '../../styles/user.css'

import { ClearTokens } from '../token'

async function userExists(username) {
    return fetch("http://localhost:3001/user/exists", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'user': username
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
    .catch(function (error) {
        return error.response.data
    })
}

export default function UserComponent({ setUsername, setUserExists, authenticated }) {
    const [username, setName] = useState()
    const [loading, setLoading] = useState(false)

    const handleSubmit = async e => {
        e.preventDefault()

        // Before starting authentication, ensure any old tokens are deleted
        ClearTokens()

        // Check if the user exists and redirect the relevant page depending on the server result
        setUsername(username)
        setLoading(true)
        let exists = await userExists(username)
        if (!userExists instanceof Boolean) {
            alert(`SERVER ERROR\n${exists}`)
            window.location.href = "/"
        }
        setLoading(false)
        setUserExists(exists)

        if (exists === true) {
            window.location.href = "/login"
        } else {
            window.location.href = "/register"
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

    if (authenticated) {
        window.location.href = "/logout"
    }

    return (
        <div className="login-wrapper">
            <div className="login-headers">
                <h1>SEEING IS BELIEVING</h1>
                <h2>Welcome to the Eye of Horus, a multi-factor biometric authentication system! Please create or login to an account below to get started</h2>
            </div>
            <div className="login-forms">
                <Form onSubmit={handleSubmit}>
                    <Form.Group controlId="formBasicText">
                        <Form.Label id="form_label">Username</Form.Label>
                        <Form.Control type="text" placeholder="Enter username" onChange={e => setName(e.target.value)}/>
                    </Form.Group>
                    {getButton()}
                </Form>
            </div>
        </div>
    )
}

UserComponent.propTypes = {
    setUsername: PropTypes.func,
    setUserExists: PropTypes.func
}