import { useState } from 'react';

export function UsernameToken() {
    const getUsername = () => {
        const userToken = JSON.parse(localStorage.getItem('username'))
        return userToken?.username
    }

    const [username, setUsername] = useState(getUsername())

    const saveUsername = userToken => {
        localStorage.setItem('username', JSON.stringify(userToken));
        setUsername(userToken.username);
    }

    return {
        setUsername: saveUsername,
        username
    }
}

export function UserExistsToken() {
    const getUserExists = () => {
        const existsToken = JSON.parse(localStorage.getItem('exists'));
        return existsToken?.exists
    }

    const [exists, setUserExists] = useState(getUserExists())

    const saveUserExists = existsToken => {
        localStorage.setItem('exists', JSON.stringify(existsToken));
        setUserExists(existsToken.exists);
    }

    return {
        setUserExists: saveUserExists,
        exists
    }
}

export function AuthenticatedToken() {
    const getAuthenticated = () => {
        const authToken = JSON.parse(localStorage.getItem('authenticated'));
        return authToken?.authenticated
    }

    const [authenticated, setAuthenticated] = useState(getAuthenticated())

    const saveAuthenticated = authToken => {
        localStorage.setItem('authenticated', JSON.stringify(authToken));
        setAuthenticated(authToken.authenticated);
    }

    return {
        setAuthenticated: saveAuthenticated,
        authenticated
    }
}

export function ClearToken(tokenName) {
    localStorage.removeItem(tokenName)
}

export function ClearTokens() {
    localStorage.clear()
}
