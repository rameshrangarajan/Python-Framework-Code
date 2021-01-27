import React ,{Component} from 'react';
import './Loader.scss';


class Loader extends Component{
    constructor(props){
        super(props);
    }
    render(){
        const { spinner } = this.props;
        if(spinner){
            return (
                <div id="cover-spin"></div>
            );
        }
        return (<div></div>);
    }
}
export default Loader;