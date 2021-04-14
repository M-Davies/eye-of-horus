import React, { useState } from 'react'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import PropTypes from 'prop-types'

import '../../styles/user.css'

import { ClearTokens } from '../token'

async function userExists(username) {
    console.log(`username on client side = ${username}`)
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
        console.log(`return data on client side = ${data}`)
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

export default function UserComponent({ setUsername, setUserExists, authenticated }) {
    const [username, setName] = useState();

    const handleSubmit = async e => {
        e.preventDefault()

        // Before starting authentication, ensure any old tokens are deleted
        ClearTokens()

        // Check if the user exists and redirect the relevant page depending on the server result
        setUsername(username)
        let exists = await userExists(username)
        setUserExists(exists)

        if (exists === true) {
            window.location.href = "/login"
        } else {
            window.location.href = "/register"
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
                    <Button variant="primary" type="submit">
                        Submit
                    </Button>
                </Form>
            </div>
        </div>
    )
}

UserComponent.propTypes = {
    setUsername: PropTypes.func,
    setUserExists: PropTypes.func
}