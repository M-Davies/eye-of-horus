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
            try {
                return error.response.data
            } catch (err) {
                return "Server error in checking if user exists, please try again later"
            }
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
        if (!username) {
            alert("Please provide a username")
        } else if (username.match(/\W/)) {
            alert("Username must consist of only number and letter characters")
        } else {
            setUsername(username)
            setLoading(true)
            let exists = await userExists(username)
            setLoading(false)
            if (!userExists instanceof Boolean) {
                alert(exists)
                window.location.href = "/"
            } else {
                setUserExists(exists)

                if (exists === true) {
                    window.location.href = "/login"
                } else {
                    window.location.href = "/register"
                }
            }
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
        window.location.href = "/dashboard"
    }

    return (
        <div className="login-wrapper">
            <div className="login-headers">
                <h1 id="sub_header">Welcome to the Eye of Horus<br></br>A multi-factor biometric authentication system</h1>
                <h2 id="username_header">Please enter a new or existing username</h2>
            </div>
            <div className="login-forms">
                <Form onSubmit={handleSubmit}>
                    <Form.Group controlId="formBasicText">
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
    setUserExists: PropTypes.func,
    authenticated: PropTypes.bool
}