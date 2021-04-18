import React, { useState } from 'react'
import Button from 'react-bootstrap/Button'
import Spinner from 'react-bootstrap/Spinner'
import PropTypes from 'prop-types'
import axios from 'axios'

import '../../styles/dashboard.css'

import { ClearTokens } from '../token'

export default function DashboardComponent({ username, authenticated }) {
    const [deleting, setDeleting] = useState(false)

    const handleDeleteClick = async e => {
        e.preventDefault()
        if (window.confirm("Are you sure you want to delete your account?")) {
            setDeleting(true)
            let params = new FormData()
            params.append("user", username)

            return await axios.post("http://localhost:3001/user/delete", params)
                .then(res => {
                    setDeleting(false)
                    if (res.status === 200) {
                        ClearTokens()
                        window.location.href = "/"
                    } else {
                        const responseData = JSON.stringify(res.data)
                        if (responseData.TYPE === undefined) {
                            alert(`${responseData}`)
                        } else {
                            alert(`${responseData.TYPE}\n${responseData.MESSAGE}`)
                        }
                        window.location.href = "/dashboard"
                    }
                })
                .catch(function (error) {
                    setDeleting(false)
                    if (error.response.data) {
                        const responseData = JSON.stringify(error.response.data)
                        if (responseData.TYPE === undefined) {
                            alert(`${responseData}`)
                        } else {
                            alert(`${responseData.TYPE}\n${responseData.MESSAGE}`)
                        }
                        window.location.href = "/dashboard"
                    } else {
                        throw new Error(error.toString())
                    }
                })
        }
    }

    if (!authenticated) {
        window.location.href = "/"
    } else {
        if (deleting) {
            return (
                <div className="dashboard-wrapper">
                    <h1>You are logged in as {username}!</h1>
                    <Spinner
                        as="span"
                        animation="grow"
                        role="status"
                        aria-hidden="true"
                    />
                        Deleting Profile...
                </div>
            )
        } else {
            return (
                <div className="dashboard-wrapper">
                    <h1>You are logged in as {username}!</h1>
                    <Button variant="primary" href="/logout" size="lg" block>Logout</Button>
                    <Button variant="warning" href="/edit" size="lg" block>Edit Profile</Button>
                    <Button variant="danger" onClick={handleDeleteClick} size="lg" block>Delete Profile</Button>
                </div>
            )
        }
    }
}

DashboardComponent.propTypes = {
    username: PropTypes.string
}
