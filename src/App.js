import StreamButton from './components/stream.js';
import './styles/App.css';

import 'bootstrap/dist/css/bootstrap.min.css';
import React, { Component } from 'react';

class App extends Component {
  render() {
    return (
      <div className="App">
        <div className="main-body">
          <StreamButton></StreamButton>
        </div>
      </div>
    );
  }
}

export default App;
