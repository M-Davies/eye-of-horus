import axios from 'axios'

export function uploadEncoded(encoded) {
    let params = new FormData()
    params.append("encoded", encoded)

    return axios.post("http://localhost:3001/upload/encoded", params)
        .then(res => {
            return Array.from(res.data)
        })
        .catch(function (error) {
            try {
                return error.response.data
            } catch (err) {
                return "Server error in uploading screenshot, please try again later"
            }
        })
}

export function uploadFiles(files) {
    let params = new FormData()

    // Uploading 1 or more files?
    if (Array.isArray(files)) {
        let count = 1
        files.forEach(file => {
            params.append(`file_${count}`, file)
            count++
        })
    } else {
        params.append(`file`, files)
    }

    // Upload and return paths
    return axios.post(`http://localhost:3001/upload/file`, params)
        .then(res => {
            return Array.from(res.data)
        })
        .catch( function (error) {
            try {
                return error.response.data
            } catch (err) {
                return "Server error in uploading files, please try again later"
            }
        })
}

export function checkIfLock(username) {
    let params = new FormData()
    params.append("user", username)

    return axios.post("http://localhost:3001/user/hasLock", params)
        .then(res => {
            if (res.status === 200) {
                return res.data
            } else {
                return JSON.stringify(res.data)
            }
        })
        .catch(function (error) {
            try {
                return error.response.data
            } catch {
                return "Server error in authenticating user, please try again later"
            }
        })
}

export function checkCombination(paths) {
    let params = new FormData()
    params.append("files", paths)

    return axios.post("http://localhost:3001/types", params)
        .then(res => {
            if (res.status === 200) {
                return Array.from(res.data)
            } else {
                return JSON.stringify(res.data)
            }
        })
        .catch(function (error) {
            try {
                return error.response.data
            } catch {
                return "Server error in checking gesture combination types"
            }
        })
}
