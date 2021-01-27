import React from 'react';
import './App.scss';
import Header from '../Components/Header/Header';
import '../Components/Header/Header.scss';
import Container from './Container';
import ContainerTrain from './ContainerTrain';
import ContainerDashboard from './ContainerDashboard';

import {
  BrowserRouter as Router,
  Route,
} from "react-router-dom";

function App() {
  return (
    <Router>
    <div className="App">
      <Header />
      <Route exact path="/" component={Container} />
      <Route exact path="/training" component={Container} />
      <Route exact path="/dashboard" component={ContainerDashboard} />
    </div>
    </Router>
  );
}

export default App;
