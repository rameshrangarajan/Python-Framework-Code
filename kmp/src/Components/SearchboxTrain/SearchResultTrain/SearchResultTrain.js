import React, { Component } from 'react';
import './SearchResultTrain.scss';
import { replace } from 'lodash';
import { Container, Row, Col, Button } from 'react-bootstrap';
import SearchResultItem from './SearchResultItemTrain/SearchResultItemTrain';
import axios from 'axios';
import { API_ROOT } from '../../../Common/api-config';
//import thumbnailImg from '../../../assets/images/thumbnail.jpg';
import Switch from "react-switch";
import { toast } from 'react-toastify';
import Pagination from '../../../Common/Pagination';

var self;

class SearchResultTrain extends Component {

    constructor(props) {
        super();
        this.state = {
            isAnySliderValChanged: false,
            isShowRatingsCheck: false,
            values: [],
            sliderData: [],
            page_no: props.pageNo,
            start_item: 1,
            page_no_change: 1
        };
        self = this;
    }

    componentWillReceiveProps(props) {
        this.setState({
            page_no: props.pageNo,
            start_item: ((this.state.page_no - 1) * 10) + 1,
            page_no_change: props.pageNo
        })
    }

    componentDidMount(){
        if(this.refs.resultsDiv){
             this.refs.resultsDiv.focus();
        }
    }
    //Training submit button click handler
    gradeSubmit = (event) => {
        event.preventDefault();
        let trainData = [];

        trainData = { "train": this.state.sliderData };

        trainData = JSON.stringify(trainData);

        axios.post(API_ROOT + '/train', trainData, { headers: { 'Content-Type': 'application/json' } })
            .then(response => {
                toast("You have successfully submitted your grading!", {
                    position: "bottom-right",
                    autoClose: 4000,
                    hideProgressBar: false,
                    closeOnClick: false,
                    pauseOnHover: false,
                    draggable: false,
                    pauseOnFocusLoss: false
                });
                this.refs.child.updateSliderValues();
            })
            .catch(error => {
                toast("You have successfully submitted your grading!", {
                    position: "bottom-right",
                    autoClose: 4000,
                    hideProgressBar: false,
                    closeOnClick: false,
                    pauseOnHover: false,
                    draggable: false,
                    pauseOnFocusLoss: false
                });
                this.refs.child.updateSliderValues();
            })
            this.updateSliderAPIData();
            this.setState({isAnySliderValChanged: false});
    }

    //Update slider value list handler
    updateSliderList = (index, value) => {
        let PrevValues = { ...this.state.values };
        PrevValues[index] = value;
        this.setState({
            isAnySliderValChanged: true,
            values: PrevValues
        })
        this.props.sliderValueLister()
    }

    //Update slider data list handler(list for sending in payload)
    updateSliderDataList = (index, value, result) => {
        let PrevData = { ...this.state.sliderData };
        if (value !== 0) {
            PrevData[index] = {
                docId: result.doc_id,
                searchQuery: this.props.searchKey,
                DateTime: new Date(),
                grade: value - 1
            };
            this.setState({
                sliderData: PrevData
            })
        }
    }


    //clear values on new search handler 
    updateSliderAPIData = () => {
        this.setState({
            isShowRatingsCheck: false,
            values: [],
            sliderData: []
        })
    }

    //Training switch handler
    handleSwitchChange = (checked) => {
        this.setState({ isShowRatingsCheck: checked });
    }

    pageNoChange = (event) => {
        this.setState({
            page_no_change: event.target.value
        })
    }

    pageNoUpdate = (event) => {
        var code = event.keyCode || event.which;
        if (code === 13) {
            let currentPage = event.target.value;
            if (currentPage !== "" && currentPage < Math.ceil(this.props.data.num_results / 10) + 1
                && currentPage > 0) {
                this.setState({
                    isAnySliderValChanged: false,
                    page_no: currentPage,
                    start_item: ((currentPage - 1) * 10) + 1,
                    page_no_change: currentPage
                });
                this.refs.resultsDiv.scrollTop = 0;
                this.updateSliderAPIData();

                this.props.pageChange(currentPage)
            }
            else {
                this.setState({
                    page_no: this.state.page_no,
                    page_no_change: this.state.page_no
                });
                toast("Please enter correct page number!", {
                    position: "bottom-right",
                    autoClose: 4000,
                    hideProgressBar: false,
                    closeOnClick: false,
                    pauseOnHover: false,
                    draggable: false,
                    pauseOnFocusLoss: false
                });
            }
        }
    }
    
    onPageChanged = (data, isByClick) => {
        let currentPage = data;
        let currentShowPage = self.state.page_no;
        if (isByClick && currentShowPage != currentPage) {
            this.setState({
                isAnySliderValChanged: false,
                page_no: currentPage,
                start_item: ((currentPage - 1) * 10) + 1,
                page_no_change: currentPage
            });
            this.updateSliderAPIData();
            this.props.pageChange(currentPage);
            this.refs.resultsDiv.scrollTop = 0;
        }
    };


    render() {
        
        let tempArr = [];
        for(let i=0;i<=this.props.data.num_results;i++){
            tempArr.push({
                'id': i+1
            })
        }

        const createResultRow = (result, index) => {

            let img;
            let thumbnails = [], context = [];
            result.occurrences.map(occurence => {
                if (thumbnails.indexOf(occurence.thumbnail_small) == -1)
                    thumbnails.push(occurence.thumbnail_small)
            });
            result.occurrences.map((occurence, index) => {
                if (context.length < 4) {
                    if (occurence.content !== "") {
                        context.push(replace(replace(occurence.content[0], '**', '<strong>'), '**', '</strong>') + '...')
                    }
                }


            });

            context = context.join(', ');
            context = context.slice(0, 200);

            thumbnails = thumbnails.slice(0, 3);
            let thumbnailList = thumbnails.map(thumbnail => {
                return <img className="ml-2 mr-2" src={thumbnail} key={index + Math.random()} width="190px" height="107px" />
            });
            img = (
                <span>
                    {thumbnailList}
                </span>
            )

            let title = result.title ? result.title : result.file_name;
            let props = {
                title: title,
                context: context,
                result: result,
                index: index,
                img: img,
                isShowRatingsCheck: this.state.isShowRatingsCheck,
                updateSliderList: this.updateSliderList,
                updateSliderDataList: this.updateSliderDataList,
                likes_count: result.num_likes,
                dislikes_count: result.num_dislikes,
                sliderValues: this.state.values,
                searchKey: this.props.searchKey,
                liked_status : result.liked_status,
                disliked_status : result.disliked_status,
                updateSearchResult: this.props.updateSearchResult,
                currentPageNo: this.state.page_no,
            }

            return (
                <SearchResultItem key={index} props={props} ref="child" />
            )
        };

        let tableData = null;
        if (this.props.results.length > 0) {
            document.body.style = "";
            document.getElementsByClassName("search-box")[0].setAttribute("style", "height: 20%");
            document.getElementsByClassName("container")[0].setAttribute("style", "top: 0%; margin-left: 0");
            document.getElementsByClassName("container-box")[0].setAttribute("style", "top: 0%;");
            document.getElementsByClassName("title")[0].setAttribute("style", "display: block");
            document.getElementsByClassName("header")[0].setAttribute("style", "background-color: #17a1cc");
            document.getElementsByClassName("search-input-row")[0].setAttribute("style", "justify-content: left !important");
            document.getElementsByClassName("react-autosuggest__input")[0].setAttribute("style", "height: 35px; float:left; margin-left:25px");
            document.getElementsByClassName("react-autosuggest__suggestions-container")[0].setAttribute("style", "margin-left:25px; margin-top:-9px");
            document.getElementsByClassName("search-btn")[0].setAttribute("style", "right: -9px");

            let submitBtn = null;

            if (this.state.isShowRatingsCheck) {
                var variant = 'secondary';

                if(this.state.isAnySliderValChanged === true) {
                    variant = 'primary';
                }
                submitBtn = (<Button style = {{marginLeft : "4px"}} variant={ variant } type="submit" onClick={this.gradeSubmit} className="trainingSubBtn mr-4" disabled = { !this.state.isAnySliderValChanged }>submit</Button>)
            }

            // logic for updating objects and checking for duplicate titles (show less/ more functionality)
            var newArr = this.props.results;


            for (var i = 0; i < newArr.length; i++) {
                if (newArr[i].title === null) {
                    newArr[i].title = newArr[i].file_name;
                }
                if(newArr[i].posIdx){
                    newArr[i].posIdx = [];
                }
            }


            var cnt = 0;
            for (var i = 0; i < newArr.length; i++) {
                for (var j = i + 1; j < newArr.length; j++) {
                    if (newArr[i].title === newArr[j].title) {
                        if (this.props.results[i].posIdx) {
                            if (!this.props.results[i].notShow) {
                                // on re render check if the array already has a reference of the duplicate record
                                if (!this.props.results[i].posIdx.includes(j))
                                    this.props.results[i].posIdx.push(j);
                                if (this.props.results[i].posIdx.includes(i))
                                    this.props.results[i].posIdx.splice(this.props.results[i].posIdx.indexOf(i),1);
                                this.props.results[j].notShow = true;
                            }

                        } else {
                            // check if the record is not already scanned for not showing
                            if (!this.props.results[i].notShow) {
                                this.props.results[i].posIdx = [];
                                this.props.results[i].posIdx.push(j);
                                this.props.results[j].notShow = true;
                            }
                        }
                    }
                }
            }

            
            let rearrangedArr = [];
            let mainArr = [...this.props.results];
            for (let ctr = 0; ctr < mainArr.length; ctr++) {
                const result = rearrangedArr.find( ({ title }) => title === mainArr[ctr].title );
                if(!result){
                    rearrangedArr.push(mainArr[ctr]);
                    if(mainArr[ctr].posIdx){
                        for(let y=0;y<mainArr[ctr].posIdx.length;y++){
                            rearrangedArr.push(mainArr[mainArr[ctr].posIdx[y]]);
                        }
                    }
                }
            }

            for(let i1=0;i1<rearrangedArr.length;i1++){
                if(rearrangedArr[i1].posIdx){
                    for(let j1=0;j1<rearrangedArr[i1].posIdx.length;j1++){
                        rearrangedArr[i1].posIdx[j1] = i1+j1+1;
                    }
                }
            }
            
            
            var windowHeight = window.innerHeight;
            var toolbarHt = document.getElementsByClassName("search-box")[0].offsetHeight;
            var contentHeight = windowHeight - toolbarHt;
            var itemHt = contentHeight-65;
            tableData = (
                <Container id="search-results" style={{ height: contentHeight+"px", overflow: 'hidden' }}>
                    <hr className="mt-0" />
                    <Row id="results-metadata">
                        <Col sm={12}>
                            <span> {this.props.data.num_results} results out of {this.props.data.number_of_documents} ({this.props.data.processing_time})</span>
                        </Col>
                    </Row>
                    
                    <div tabIndex={0} className="container-fluid search-result-focus" ref="resultsDiv" style = { { height: itemHt+"px", overflow: 'auto'} }>
                        {rearrangedArr.map(createResultRow, this)}
                        <span className="page-count-range">{this.state.start_item}-{Math.ceil(this.props.data.num_results / 10) === this.state.page_no ? this.props.data.num_results : (this.state.start_item - 1) + 10} of  {this.props.data.num_results}</span>
                        <div className="mt-2 mb-2">
                            <Pagination items={tempArr} onChangePage={this.onPageChanged} initialPage={this.state.page_no} />
                        </div>
                    </div>
                    
                </Container>)
        }

        if (this.props.error) {
            tableData = <div className="alert alert-danger mt-5" role="alert">Sorry! we could not find any search result for this term. Please try something else.</div>;
        }

        return (
            <div>
                {tableData}
            </div>
        )
    }
}

export default SearchResultTrain
