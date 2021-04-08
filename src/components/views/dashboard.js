import React from 'react'
import PropTypes from 'prop-types';

export default function UserComponent({ username }) {
    return (
        <h1>Welcome {username}</h1>
    )
}

UserComponent.propTypes = {
    username: PropTypes.string.isRequired
}
