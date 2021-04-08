import { useState } from 'react';

export default function TokenComponent() {
    const getUserExist = () => {
        const userExists = Boolean(localStorage.getItem('exists'));
        return Boolean(userExists?.exists)
    }

    const [exists, setUserExists] = useState(getUserExist())

    const saveUserExist = userExists => {
        localStorage.setItem('exists', Boolean(userExists));
        setUserExists(Boolean(userExists.exists));
    }

    return {
        setUserExists: saveUserExist,
        exists
    }
}
