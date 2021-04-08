import React, { Component } from 'react'
import Navbar from 'react-bootstrap/Navbar'
import Nav from 'react-bootstrap/Nav'

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
              className="d-inline-block align-top"
            />{' '}
            Eye Of Horus
            </Navbar.Brand>
          <Navbar.Collapse className="justify-content-end">
            <Nav className="auto">
              <Nav.Link href="/login">Signed in as: User</Nav.Link>
            </Nav>
          </Navbar.Collapse>
        </Navbar>
      </div>
    )
  }
}
