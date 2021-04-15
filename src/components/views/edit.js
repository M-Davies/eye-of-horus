import React from 'react'
import PropTypes from 'prop-types'

export default function EditComponent({ username, authenticated }) {

    if (!authenticated) {
        window.location.href = "/"
        alert("You need to be logged in to view this page")
    }

    return (
        <div className="dashboard-wrapper">
            <h1>Edit Page</h1>
        </div>
    )
}

EditComponent.propTypes = {
    username: PropTypes.string.isRequired
}
