import NavbarComponent from './components/views/navbar'
import UserComponent from './components/views/user'
import AuthenticateComponent from './components/views/authenticate'
import DashboardComponent from './components/views/dashboard'
import EditComponent from './components/views/edit'
import LogoutComponent from './components/views/logout'
import ForgotComponent from './components/views/forgot'
import { UsernameToken } from './components/token'

import './styles/App.css'

import 'bootstrap/dist/css/bootstrap.min.css'
import React from 'react'
import { BrowserRouter, Route, Switch } from 'react-router-dom'

export default function App() {
    const { username, setUsername } = UsernameToken()

    return (
        <BrowserRouter>
            <div className="app">
                <div className="nav-container">
                    <NavbarComponent username={username} />
                </div>
                <div className="main-container">
                    <Switch>
                        <Route exact path="/">
                            <UserComponent
                                setUsername={setUsername}
                            />
                        </Route>
                        <Route path="/register">
                            <AuthenticateComponent
                                username={username}
                                registering={true}
                            />
                        </Route>
                        <Route path="/login">
                            <AuthenticateComponent
                                username={username}
                                registering={false}
                            />
                        </Route>
                        <Route path="/dashboard">
                            <DashboardComponent
                                username={username}
                            />
                        </Route>
                        <Route path="/edit">
                            <EditComponent
                                username={username}
                            />
                        </Route>
                        <Route path="/logout">
                            <LogoutComponent
                                username={username}
                            />
                        </Route>
                        <Route path="/forgot">
                            <ForgotComponent
                                username={username}
                            />
                        </Route>
                    </Switch>
                </div>
            </div>
        </BrowserRouter>
    )
}
