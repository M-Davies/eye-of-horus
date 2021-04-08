import React, { useState } from 'react'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import PropTypes from 'prop-types';

import '../../styles/login.css'

async function userExists(username) {
    return fetch(`http://localhost:3001/login/exists`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(username)
    })
    .then(data => data.json())
    .then(data => {
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

export default function UserComponent({ setUserExists }) {
    const [username, setUserName] = useState();

    const handleSubmit = async e => {
        e.preventDefault()

        const exists = await userExists({username})
        setUserExists(exists)
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
                        <Form.Control type="text" placeholder="Enter username" onChange={e => setUserName(e.target.value)}/>
                    </Form.Group>
                    <Button variant="primary" type="submit" onClick={handleSubmit}>
                        Submit
                    </Button>
                </Form>
            </div>
        </div>
    )
}

UserComponent.propTypes = {
    setUserExists: PropTypes.func.isRequired
}