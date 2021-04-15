import React from 'react'
import Button from 'react-bootstrap/Button'
import PropTypes from 'prop-types'

export default function DashboardComponent({ username, authenticated }) {

    if (!authenticated) {
        window.location.href = "/"
        alert("You need to be logged in to view this page")
    }

    return (
        <div className="dashboard-wrapper">
            <h1>You are logged in as {username}!</h1>
            <Button variant="primary" href="/logout" size="lg" block>Logout</Button>
            <Button variant="warning" href="/edit/face" size="lg" block>Edit User Face</Button>
            <Button variant="warning" href="/edit/lock" size="lg" block>Edit Lock Gesture</Button>
            <Button variant="warning" href="/edit/unlock" size="lg" block>Edit Unlock Gesture</Button>
            <Button variant="danger" href="/delete" size="lg" block>Delete Account</Button>
        </div>
    )
}

DashboardComponent.propTypes = {
    username: PropTypes.string
}
