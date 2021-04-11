import React, { Component } from 'react'
import Navbar from 'react-bootstrap/Navbar'
import Nav from 'react-bootstrap/Nav'
import PropTypes from 'prop-types'

function profileText(username) {
    if (!username) {
        return (
            <Nav.Link href="/login">Sign In</Nav.Link>
        )
    } else {
        return (
            <Nav.Link href="/logout">Logged in as: {username}</Nav.Link>
        )
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
                        {profileText(this.props.username)}
                    </Nav>
                    </Navbar.Collapse>
                </Navbar>
            </div>
        )
    }
}

NavbarComponent.propTypes = {
    username: PropTypes.string
}

NavbarComponent.defaultProps = {
    username: null
}