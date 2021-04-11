import NavbarComponent from './components/views/navbar'
import UserComponent from './components/views/user'
import AuthenticateComponent from './components/views/authenticate'
import DashboardComponent from './components/views/dashboard'
import { UsernameToken, UserExistsToken, AuthenticatedToken } from './components/token'

import './styles/App.css'

import 'bootstrap/dist/css/bootstrap.min.css'
import React from 'react'
// import { BrowserRouter, Route, Switch } from 'react-router-dom'

export default function App() {
    const { username, setUsername } = UsernameToken()
    const { userExists, setUserExists } = UserExistsToken()
    const { authenticated, setAuthenticated } = AuthenticatedToken()

    if(!username) {
        return (
            <div className="app">
                <div className="nav-container">
                    <NavbarComponent username={username}/>
                </div>
                <div className="user-wrapper">
                    <UserComponent setUsername={setUsername} setUserExists={setUserExists} />
                </div>
            </div>
        )
    } else if (!userExists) {
        return (
            <div className="app">
                <div className="nav-container">
                    <NavbarComponent username={username}/>
                </div>
                <div className="register-wrapper">
                    <AuthenticateComponent
                        username={username}
                        setUserExists={setUserExists}
                        setAuthenticated={setAuthenticated}
                        registering={true}
                    />
                </div>
            </div>
        )
    } else if (!authenticated) {
        return (
            <div className="app">
                <div className="nav-container">
                    <NavbarComponent username={username}/>
                </div>
                <div className="login-wrapper">
                    <AuthenticateComponent
                        username={username}
                        setUserExists={setUserExists}
                        setAuthenticated={setAuthenticated}
                        registering={false}
                    />
                </div>
            </div>
        )
    } else {
        return (
            <div className="app">
                <div className="nav-container">
                    <NavbarComponent username={username}/>
                </div>
                <div className="dashboard-wrapper">
                    <DashboardComponent username={username}/>
                </div>
            </div>
        )
    }
}
