import NavbarComponent from './components/navbar'
import LoginComponent from './components/login'
import DashboardComponent from './components/dashboard'
import Token from './components/token'

import './styles/App.css'

import 'bootstrap/dist/css/bootstrap.min.css'
import React from 'react'
import { BrowserRouter, Route, Switch } from 'react-router-dom'

export default function App() {
    const { token, setToken } = Token();

    if(!token) {
        return (
            <div className="anon-wrapper">
                <NavbarComponent></NavbarComponent>
                <LoginComponent setToken={setToken} />
            </div>
        )
    }

    return (
        <div className="App">
            <div className="nav-container">
                <NavbarComponent></NavbarComponent>
            </div>
            <div className="main-container">
                <BrowserRouter>
                    <Switch>
                        <Route path="/dashboard">
                            <DashboardComponent></DashboardComponent>
                        </Route>
                    </Switch>
                </BrowserRouter>
            </div>
        </div>
    )
}
