import React from 'react'
import PropTypes from 'prop-types'

export default function EditComponent({ username, authenticated }) {

    if (!authenticated) {
        window.location.href = "/"
    } else {
        return (
            <div className="edit-wrapper">
                <h1>Edit Page</h1>
            </div>
        )
    }
}

EditComponent.propTypes = {
    username: PropTypes.string.isRequired
}
