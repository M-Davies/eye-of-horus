import React, { Component } from 'react'
import Navbar from 'react-bootstrap/Navbar'
import Nav from 'react-bootstrap/Nav'
import PropTypes from 'prop-types'

import '../../styles/navbar.css'

function profileText(username, authenticated) {
    if (!username) {
        return (
            <Nav.Item id="nav_user">Not Signed In</Nav.Item>
        )
    } else {
        if (authenticated === true) {
            return (
                <Nav.Item id="nav_user">Logged in as: {username}</Nav.Item>
            )
        } else {
            return (
                <Nav.Item id="nav_user">Logging in {username}</Nav.Item>
            )
        }
    }
}

export default class NavbarComponent extends Component {
    render() {
        return (
            <div className="navbar-wrapper">
                <Navbar bg="dark" variant="dark">
                    <Navbar.Brand href="/">
                        <img
                            alt=""
                            src="/eye-of-horus.png"
                            width="30"
                            height="30"
                            className="eye-logo"
                        />
                        {' '} Eye Of Horus
                    </Navbar.Brand>
                    <Navbar.Collapse className="justify-content-end">
                    <Nav className="auto">
                        {profileText(this.props.username, this.props.authenticated)}
                    </Nav>
                    </Navbar.Collapse>
                </Navbar>
            </div>
        )
    }
}

NavbarComponent.propTypes = {
    username: PropTypes.string,
    authenticated: PropTypes.bool
}

NavbarComponent.defaultProps = {
    username: null,
    authenticated: false
}