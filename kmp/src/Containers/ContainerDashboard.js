import React, { Component } from 'react';
import Dashboard from '../Components/Dashboard/Dashboard';
import '../Components/Dashboard/Dashboard.scss';

class ContainerDashboard extends Component {

    render() {
        return (
           <div className="container-box">
                <Dashboard/>
            </div>
        );
    }
}

export default ContainerDashboard;