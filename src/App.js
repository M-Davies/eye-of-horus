import NavbarComponent from './components/views/navbar'
import UserComponent from './components/views/user'
import AuthenticateComponent from './components/views/authenticate'
import DashboardComponent from './components/views/dashboard'
import { UsernameToken, UserExistsToken, AuthenticatedToken } from './components/token'

import './styles/App.css'

import 'bootstrap/dist/css/bootstrap.min.css'
import React from 'react'
import { BrowserRouter, Route, Switch } from 'react-router-dom'

export default function App() {
    const { username, setUsername } = UsernameToken()
    const { userExists, setUserExists } = UserExistsToken()
    const { authenticated, setAuthenticated } = AuthenticatedToken()

    return (
        <BrowserRouter>
            <div className="app">
                <div className="nav-container">
                    <NavbarComponent username={username}/>
                </div>
                <div className="main-container">
                    <Switch>
                        <Route exact path="/">
                            <UserComponent
                                setUsername={setUsername}
                                setUserExists={setUserExists}
                            />
                        </Route>
                        <Route path="/register">
                            <AuthenticateComponent
                                username={username}
                                setUserExists={setUserExists}
                                setAuthenticated={setAuthenticated}
                                registering={true}
                            />
                        </Route>
                        <Route path="/login">
                            <AuthenticateComponent
                                username={username}
                                setUserExists={setUserExists}
                                setAuthenticated={setAuthenticated}
                                registering={false}
                            />
                        </Route>
                        <Route path="/dashboard">
                            <DashboardComponent/>
                        </Route>
                    </Switch>
                </div>
            </div>
        </BrowserRouter>
    )
}
