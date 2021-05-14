import { useState } from 'react';

export function UsernameToken() {
    const getUsername = () => {
        const userToken = JSON.parse(localStorage.getItem('username'))
        return userToken
    }

    const [username, setUsername] = useState(getUsername())

    const saveUsername = userToken => {
        localStorage.setItem('username', JSON.stringify(userToken))
        setUsername(userToken)
    }

    return {
        setUsername: saveUsername,
        username
    }
}

export function ClearToken(tokenName) {
    localStorage.removeItem(tokenName)
}

export function ClearTokens() {
    localStorage.clear()
}
