import React, { Component } from 'react';
import Searchbox from '../Components/Searchbox/Searchbox';
import '../Components/Searchbox/Searchbox.scss';

class Container extends Component {

    render() {
        return (
            <div className="container-box">
                <Searchbox />
            </div>
        );
    }
}

export default Container;