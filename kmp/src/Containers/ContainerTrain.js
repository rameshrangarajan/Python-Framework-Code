import React, { Component } from 'react';
import SearchboxTrain from '../Components/SearchboxTrain/SearchboxTrain';
import '../Components/SearchboxTrain/SearchboxTrain.scss';

class ContainerTrain extends Component {

    render() {
        return (
            <div className="container-box">
                <SearchboxTrain />
            </div>
        );
    }
}

export default ContainerTrain;