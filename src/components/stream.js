import React, { Component } from 'react'
import Button from 'react-bootstrap/Button'

class Stream extends Component {
    constructor(props) {
        super(props);
        this.state = { apiResponse: "" };
    }

    startStream() {
        fetch("/stream.")
            .then(res => res.text())
                .then(res => this.setState({ apiResponse: res }));
    }
}