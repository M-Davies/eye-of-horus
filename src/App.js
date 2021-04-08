import NavbarComponent from './components/views/navbar'
import UserComponent from './components/views/user'
import DashboardComponent from './components/views/dashboard'
import RegisterComponent from './components/views/register'
import LoginComponent from './components/views/register'
import TokenComponent from './components/token'

import './styles/App.css'

import 'bootstrap/dist/css/bootstrap.min.css'
import React from 'react'
import { BrowserRouter, Route, Switch } from 'react-router-dom'

export default function App() {
    const { userExists, setUserExists } = TokenComponent()

    if(!userExists) {
        return (
            <div className="anon-wrapper">
                <NavbarComponent />
                <UserComponent setUserExists={setUserExists} />
            </div>
        )
    }

    return (
        <div className="App">
            <div className="nav-container">
                <NavbarComponent />
            </div>
            <div className="main-container">
                <BrowserRouter>
                    <Switch>
                        <Route path="/dashboard">
                            <DashboardComponent />
                        </Route>
                        <Route path="/register">
                            <RegisterComponent />
                        </Route>
                        <Route path="/login">
                            <LoginComponent />
                        </Route>
                    </Switch>
                </BrowserRouter>
            </div>
        </div>
    )
}
