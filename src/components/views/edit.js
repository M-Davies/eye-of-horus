import React from 'react'
import PropTypes from 'prop-types'

export default function EditComponent({ username }) {
    return (
        <div className="dashboard-wrapper">
            <h1>Edit Page</h1>
        </div>
    )
}

EditComponent.propTypes = {
    username: PropTypes.string.isRequired
}
