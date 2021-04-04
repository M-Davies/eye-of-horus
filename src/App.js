import NavbarComponent from './components/navbar'
import LoginComponent from './components/login'

import './styles/App.css';

import 'bootstrap/dist/css/bootstrap.min.css';
import React, { Component } from 'react';
import Dropdown from 'react-bootstrap/Dropdown'

export default class App extends Component {
  render() {
    return (
      <div className="App">
        <div className="nav-container">
          <NavbarComponent></NavbarComponent>
        </div>
        <div className="main-container">
          <h1 id="home_header">SEEING IS BELIEVING</h1>
          <Dropdown.Divider />
          <h2 id="home_subheader">Welcome to the Eye of Horus, a multi-factor biometric authentication system! Please create or login to an account below to get started</h2>
          <LoginComponent></LoginComponent>
        </div>
      </div>
    )
  }
}
