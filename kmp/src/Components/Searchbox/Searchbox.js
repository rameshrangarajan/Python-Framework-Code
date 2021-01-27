import React, { Component } from 'react';
import axios from 'axios';
import Autosuggest from 'react-autosuggest';
import AutosuggestHighlightMatch from 'autosuggest-highlight/umd/match';
import AutosuggestHighlightParse from 'autosuggest-highlight/umd/parse';
import FontAwesome from 'react-fontawesome';
import SearchResult from './SearchResult/SearchResult';
import { isEmpty } from 'lodash';
import { API_ROOT } from '../../Common/api-config'
import { Container, Row, Col, Form, Button, Modal } from 'react-bootstrap';
import backgroundImage from '../../assets/images/appBackground.png';
import Switch from "react-switch";
import Loader from '../Loader/Loader';
import { Label } from 'semantic-ui-react'
import svgImg from '../../assets/images/svg-img.png';
import StarRatings from 'react-star-ratings';
import { toast } from 'react-toastify';

var self;

class Searchbox extends Component {

    constructor(props) {
        super(props);
        this.state = {
            value: '',
            searchResult: [],
            suggestions: [],
            suggestionList: [],
            isValid: true,
            error: false,
            data: [],
            isLoaded: false,
            results: [],
            page_number: 1,
            textVal:"",
            showTrainingPanel: false,
            isShowRatingsCheck:false,
            isAnySliderValChanged: false,
            loading:'',
            showFilter:false,
            selectedValue:'all',
            filterError:false,
            showFooterBar:false,
            showSlider:false,
            trending_queries:[],
            showTrendingSearch:false,
            onSubmitValue:'',
            enteredValue:'',
            trending_topics:[],
            trending_documents:[],
            setTopMarginForSearch:false,
            showFeedbackModal:false,
            rating:0,
            feedback:''
        };
        self = this;
        let keys = [];
        // to get current url
         let url = window.location.href
         sessionStorage.setItem('url',url);

         let session;
         if(sessionStorage.getItem('url') === API_ROOT+"/training"){
             this.session = 'training';
         }
        
        // for local machine
        //   if(sessionStorage.getItem('url') == "http://localhost:8080/training"){
        //      this.session = 'training'
        //  }
    }

    //Search button click event function
    onSearchBtnClick = (event) => {
        event.preventDefault();
        let value = this.state.value.trim();  //to remove white spaces
        let newVal = this.input.value.trim();
        if (!isEmpty(newVal)) { //If search field is not empty

            this.setState({
                page_number: 1,
                loading:true,
                selectedValue:'all',
                showTrendingSearch:false,
                onSubmitValue:newVal
            });
            let searchAPIData = {
                'query': newVal,
                'page_number': 1,
                'query_type' : 'search',
                'time_filter' : 'all'
            }
            this.refs.child.updateSliderAPIData();
            if(this.session == "training"){
                this.setState({
                    isShowRatingsCheck: true,
                    showFooterBar:true,
                    showSlider:true
                });
            }
            searchAPIData = JSON.stringify(searchAPIData);
            axios.post(API_ROOT + '/search', searchAPIData, { headers: { 'Content-Type': 'application/json' } })
                .then(response => {
                    if (response.data.status) { //If status key is present (show error)
                        this.setState({
                            error: true,
                            searchResult: [],
                            loading:false,
                            showFilter:false,
                        })
                    } else { //If status key is not present
                        let fileArray = response.data.results[0].slice(0, 10);
                        this.setState({
                            searchResult: []
                        }, () => {
                            this.setState({
                                results: response.data.results[0],
                                data: response.data,
                                isValid: true,
                                error: (fileArray.length > 0) ? false : true,
                                searchResult: (fileArray.length > 0) ? fileArray : [],
                                loading:false,
                                showFilter:true,
                                filterError:false ,
                                showTrendingSearch : false,
                                setTopMarginForSearch:true
                            })
                            this.saveToStorage(this.state.onSubmitValue.trim());
                        })

                    }
                })
                .catch(error => {
                    console.log(error);
                    this.setState({ loading : false,showFilter:false,showTrendingSearch:true});
                })
                this.input.blur();
        }
        else { //Search field is empty (show invalid error).
            this.setState({
                isValid: false,
                searchResult: [],
                loading:false
            })
        }

    };


    recoverHistory = () => {
        //parse the localstorage value
        let a = localStorage.getItem('history');
        let data = JSON.parse(a);
        if (data)
            this.setState({
                history: data,
                suggestionList: data,
                suggestions: data
            });
    }

    saveToStorage = addToHistory => {
        let history = this.state.history ? this.state.history : [];
        const found = history.some(el => el.name === addToHistory);
        if (!found) {
            if (history.length >= 5) {
                history.pop();
            }
            history.unshift({ name: addToHistory });
            localStorage.setItem('history', JSON.stringify(history));
        }
    }

    //Onchange of input value function(search key)
    onChange = (event, { newValue }) => {       
        this.setState({
            value: newValue,
            isValid: true,
            error:false,
        });
        if(!this.state.isValid || this.state.error){
            this.setState({
                showFilter:false
            })
        }
        if(newValue.length === 0){
            this.recoverHistory();
        }
        
        if(newValue.length <= 2 > 0 ){
            let a = localStorage.getItem('history');
            let data = JSON.parse(a);
            const regex = new RegExp("^"+newValue,'g');
    
            let filteredData =  data.filter(function(val) {
                return (val.name).match(regex);
            });

            if(filteredData.length > 0){
                this.setState({
                    history: filteredData,
                    suggestionList: filteredData,
                    suggestions: filteredData
                });
            } else {
                filteredData.length = 0 ;
                this.setState({
                    history: filteredData,
                    suggestionList: filteredData,
                    suggestions: filteredData
                }) 
            }
        }
    };

    //Teach Autosuggest how to calculate suggestions for any given input value.
    getSuggestions = value => {
        const inputValue = value.trim().toLowerCase();
        const inputLength = inputValue.length;

        let slist = [];
        let suggestionArray = [];
        this.setState({ suggestionList: []});
        if((this.state.isvalid) || this.state.error){
            this.setState({
                showFilter:false
            })
        }
        if (inputLength >= 3) {
            return axios.post(API_ROOT + '/suggest', { 'query': value })
                .then(response => {

                    suggestionArray = response.data.related_keywords;

                    if(response.data.failure || this.state.value !== response.data.query){
                        slist = [];
                    } else {
                        suggestionArray.map(element => {
                            slist.push({ name: element })
                        })
                    }
                  
                    this.setState({
                        suggestionList: slist,
                        suggestions: slist
                    })

                })
                .catch(error => {
                    this.setState({filterError:false})
                    console.log(error)
                });
        }
        else {
            //this.setState({ suggestionList: [], suggestions: [] });
             if(this.state.suggestions.length === 0 && value !== '') {
                 this.recoverHistory();
             }
        }
    };

    //on page change event function
   /* pageChange = (currentPage) => {
        currentPage = Number(currentPage);
        let totalResults = this.state.data.num_results
        let startItem = (currentPage - 1) * 10;
        let endItem = Math.ceil(totalResults / 10) === currentPage ? totalResults : (startItem - 1) + 11
        let searchResults = this.state.results.slice(startItem, endItem);

        this.setState({
            page_number: currentPage,
            searchResult: searchResults
        });

        document.getElementById("search-results").scrollTop = 0;
    } */
    
    pageChange = (currentPage) => {
        this.setState({
            page_number: currentPage,
            loading : true,
            searchResult: this.state.results.splice((currentPage - 1) * 10 + 1,10)
            
        })
        let searchAPIData = {
            'query': this.state.onSubmitValue.trim(),
            'page_number': currentPage,
            'query_type' : 'navigation',
            'time_filter' : this.state.selectedValue
        }

        searchAPIData = JSON.stringify(searchAPIData);
        axios.post(API_ROOT + '/search', searchAPIData, { headers: { 'Content-Type': 'application/json' } })
            .then(response => {
                if (response.data.status) { //If status key is present (show error)
                    this.setState({
                        error: true,
                        searchResult: [],
                        loading:false
                    })
                } else { //If status key is not present
                    let fileArray = response.data.results[0];
                    this.setState({
                        searchResult: [],
                        loading:false
                    }, () => {
                        this.setState({
                            results: response.data.results[0],
                            data: response.data,
                            isValid: true,
                            error: (fileArray.length > 0) ? false : true,
                            searchResult: (fileArray.length > 0) ? fileArray : [],
                            loading:false,
                            showTrendingSearch:false,
                            setTopMarginForSearch:true
                        })
                    })

                }
            })
            .catch(error => {
                console.log(error)
                this.setState({ loading : false});
            })
    }

    //Autosuggest will call this function every time you need to update suggestions.
    //You already implemented this logic above, so just use it.
    onSuggestionsFetchRequested = ({ value }) => {
        this.getSuggestions(value)
        self.setState({
            textVal: value
        })
    };

    shouldRenderSuggestions = (value) => {
        return value.length >= 0;
    }

    //Autosuggest will call this function every time you need to clear suggestions.
    onSuggestionsClearRequested = () => {
        this.setState({
            suggestions: []
        });

    };

    // This function will get called 
    // to log the details related to autosuggest usage
    onSuggestionSelection = (suggestionValue,suggestionIndex) => {
        suggestionValue = suggestionValue.trim().toLowerCase();
        let dateTime = new Date();
        let searchAPIData = {
            'search_query': this.state.enteredValue.trim(),
            'autosuggest_index': suggestionIndex,
            'matched_query': suggestionValue,
            'timestamp': dateTime
        }
        return axios.post(API_ROOT + '/log_event_autosuggest_selection', searchAPIData, { headers: { 'Content-Type': 'application/json' } })
            .then(response => {
                console.log(response)
            })
            .catch(error => {
                console.log(error)
            });
        }
    
    // Autosuggest will call this function every time on selection of keywords from autosuggested options
    onSuggestionSelected = (event, { suggestionValue, suggestionIndex }) =>{
        //console.log(suggestionValue);
        this.onSuggestionSelection(suggestionValue, suggestionIndex);
    }
    //When suggestion is clicked, Autosuggest needs to populate the input
    //based on the clicked suggestion. Teach Autosuggest how to calculate the
    //input value for every given suggestion.
    getSuggestionValue = suggestion => {
        return suggestion.name
    };

    //Remove suggestion from suggestion list handler
    removeSuggestion = (event, suggestion) => {
        event.stopPropagation()
        let getIndex = (value, arr, prop) => {
            for (var i = 0; i < arr.length; i++) {
                if (arr[i][prop].toLowerCase() === value.toLowerCase()) {
                    return i;
                }
            }
        }

        let index = getIndex(suggestion.name, this.state.suggestions, 'name');
        const suggestions = [...this.state.suggestions];
        suggestions.splice(index, 1);
        this.setState({ suggestions: suggestions });
    }

    //Function for rendering suggestions.
    renderSuggestion = (suggestion, { query }) => {
        const matches = AutosuggestHighlightMatch(suggestion.name, query);
        const parts = AutosuggestHighlightParse(suggestion.name, matches);

        return (
            <div>
                <span>
                    {parts.map((part, index) => {
                        const className = part.highlight ? 'react-autosuggest__suggestion-match' : null;

                        return (
                            <span className={className} key={index}>
                                {part.text}
                            </span>
                        );
                    })}
                </span>
                {/* <FontAwesome onClick={(e) => this.removeSuggestion(e, suggestion)} className="fa fa-times float-right grey" name="fa-times" /> */}
            </div>
        );
    };
    componentDidMount() {
        document.body.style.backgroundImage = 'url(' + backgroundImage + ')';
        document.body.style.backgroundRepeat = 'no-repeat';
        document.body.style.backgroundSize = 'cover',
            document.body.style.backgroundPosition = 'center',
            document.body.style.position = 'relative',
            document.body.style.backgroundColor = "#cccccc"
        document.getElementsByClassName('react-autosuggest__input')[0].addEventListener("click", function () {
            if(self.state.textVal.length === 0)
                self.recoverHistory();
        }, false);

        this.getQueries();
        this.getTopics();
        this.getRecentDocuments();
    }

    componentDidUpdate(){
        if(this.state.setTopMarginForSearch === true){
            document.getElementsByClassName("container-box")[0].setAttribute("style", "top: 0% !important;");
        }
    }

    handleSwitchChange = (checked) => {
        this.setState({ isShowRatingsCheck: checked });
        this.refs.child.handleSwitchChange(checked);
        
        if(checked === false) {
            this.refs.child.updateSliderAPIData();
        }
    }

    gradeSubmit = (event) => {
        this.refs.child.gradeSubmit(event);
        this.setState({isAnySliderValChanged: false});
        this.setState({ isShowRatingsCheck: false });
    }

    sliderValueLister = () => {
        if(this.session === "training"){
            this.setState({isAnySliderValChanged: true})
        } 
    }
   
    updateSearchResult(docId, likes_cnt, dislikes_cnt, flag){
        var searchResultLatest = self.state.searchResult;
        let obj = searchResultLatest.find(x => x.doc_id === docId);
        let index = searchResultLatest.indexOf(obj);
        if(index >= 0){
            searchResultLatest[index].num_likes = likes_cnt;
            searchResultLatest[index].num_dislikes = dislikes_cnt;
            searchResultLatest[index].liked_status = flag;
            searchResultLatest[index].disliked_status = !flag;
            
            self.setState({
                searchResult: searchResultLatest
            })
        }
        
    }

    handleFilter(time_filter){
        let value = this.state.onSubmitValue.trim();  //to remove white spaces

        if (!isEmpty(value)) { //If search field is not empty

            this.setState({
                page_number: 1,
                loading:true,
                selectedValue: time_filter
            });

            let searchAPIData = {
                'query': this.state.onSubmitValue.trim(),
                'page_number': 1,
                'query_type' : 'filter',
                'time_filter' : time_filter
            }
            this.refs.child.updateSliderAPIData();
            searchAPIData = JSON.stringify(searchAPIData);
            axios.post(API_ROOT + '/search', searchAPIData, { headers: { 'Content-Type': 'application/json' } })
                .then(response => {
                    if (response.data.status) { //If status key is present (show error)
                        this.setState({
                            filterError: true,
                            searchResult: [],
                            loading:false
                        })
                    } else { //If status key is not present
                        let fileArray = response.data.results[0].slice(0, 10);
                        this.setState({
                            searchResult: []
                        }, () => {
                            this.setState({
                                results: response.data.results[0],
                                data: response.data,
                                isValid: true,
                                filterError: (fileArray.length > 0) ? false : true,
                                searchResult: (fileArray.length > 0) ? fileArray : [],
                                loading:false,
                                showFilter:true,
                                showTrendingSearch:false,
                                setTopMarginForSearch:true
                            })
                            this.saveToStorage(this.state.onSubmitValue.trim());
                        })

                    }
                })
                .catch(filterError => {
                    console.log(filterError);
                    this.setState({ loading : false});
                })
                this.input.blur();
        }
        else { //Search field is empty (show invalid error).
            this.setState({
                isValid: false,
                searchResult: [],
                loading:false,
                showFilter:false
            })
        }

    }

    isActive(value){
        return 'btn btn-sm btn-light btn-custom '+((value===this.state.selectedValue) ?'active':'');
      }

    // to get trending queries this function get call every time at component mounting
    getQueries(){
        this.setState({
            showTrendingSearch:true
        });
        axios.post(API_ROOT + '/get_queries_metrics', '', { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            if (response.data.trending_queries) { 
                this.setState({
                    trending_queries : (response.data.trending_queries)?response.data.trending_queries:[]
                })
            }
        })
        .catch(error => {
            console.log(error);
            this.setState({
                showTrendingSearch : false
            })
        })  
    }

    getTopics(){
        axios.post(API_ROOT + '/get_topics', '', { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            if (response.data.topics) { 
                this.setState({
                    trending_topics : (response.data.topics) ? response.data.topics : []
                })
            }
        })
        .catch(error => {
            console.log(error);
            this.setState({
                showTrendingSearch : false
            })
        })  
    }

    getRecentDocuments(){
        axios.post(API_ROOT + '/get_recent_documents', '', { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            if (response.data) { 
                this.setState({
                    trending_documents : (response.data) ? response.data : []
                })
            }
        })
        .catch(error => {
            console.log(error);
            this.setState({
                showTrendingSearch : false
            })
        })  
    }

     onTrendingSearchClick = (clickedValue)=>{
        this.setState({
            value : clickedValue
        },()=>{
            this.onSearchBtnClick(event);
        })
     }
     
     keyDown = (event)=>{
      if(event.keyCode === 8 && this.state.value.length == 0){
          event.preventDefault();
      }
     
      let charCode = event.keyCode;
      if((charCode > 64 && charCode < 91) || (charCode > 96 && charCode < 123) || charCode != 13 && charCode != 37 && charCode != 38 && charCode != 39 && charCode != 40){
        let keyvalue = this.input.value + String.fromCharCode(event.keyCode);
        keyvalue = keyvalue.replace(/[^a-zA-Z ]/g, "").toLowerCase();
        //console.log(keyvalue)
        this.setState({enteredValue : keyvalue});
      }
     
     }

     showModal = ()=>{
         this.setState({
             showFeedbackModal : true
         })
     }

     closeFeedbackModal = ()=>{
         this.setState({
            showFeedbackModal : false
         })
     }
     changeRating = ( newRating, name )=> {
        this.setState({
          rating: newRating
        });
      }


    onSubmitFeedback = (event)=>{
       let ratingVal = this.state.rating;
       let feedbackText = this.state.feedback;

       let feedbackAPIData = {
        'star_ratings': ratingVal,
        'feedback_message': feedbackText,
        'DateTime' : new Date()
    }

       axios.post(API_ROOT + '/subjective_feedback', feedbackAPIData )
                .then(response => {
                    if(response){
                        this.setState({
                            showFeedbackModal: false,
                            rating:0,
                            feedback:''
                        })
                        toast("Thank You. You have successfully submitted your feedback!", {
                            position: "bottom-right",
                            autoClose: 4000,
                            hideProgressBar: false,
                            closeOnClick: false,
                            pauseOnHover: false,
                            draggable: false,
                            pauseOnFocusLoss: false
                        });
                    }
                })
                .catch(error => {
                    this.setState({filterError:false})
                    console.log(error)
                });

    }

    handleFeedbackChange = (event)=>{
        this.setState({feedback: event.target.value.trim()});
    }

    render() {
        const { value, searchResult, suggestions, suggestionList, isValid, error, data, isLoaded } = this.state;

        const inputProps = {
            placeholder: 'Type a keyword here..',
            value : value,
            onChange: this.onChange,
            placeholder: 'Search',
            autoFocus: true,
            tabIndex: 0,
            onKeyDown:this.keyDown
        };
        let showSearchResult = null
        if (isValid) {
            showSearchResult = (
                <div>
                    <SearchResult ref="child"
                        results={searchResult}
                        data={data}
                        error={error}
                        searchKey={this.state.onSubmitValue}
                        pageNo={this.state.page_number}
                        pageChange={this.pageChange}
                        sliderValueLister = {this.sliderValueLister}
                        updateSearchResult = {this.updateSearchResult}
                        filterError={this.state.filterError}
                        session={this.session}
                        showFooterBar={this.state.showFooterBar}
                        showSlider={this.state.showSlider}
                        onTrendingSearchClick={this.onTrendingSearchClick}
                        onSubmitValue={this.state.onSubmitValue}
                        />
                </div>
            );
        } else {
            showSearchResult = (
                <div className="alert alert-danger alert-margin" role="alert">Please enter a search key!</div>
            );
        }
        return (
            <div className="h-100">
                <section className="search-box">
                    <Container>
                        <Row className="justify-content-center">
                            <Col sm={7}>
                                <div className="app-title mb-4">Knowledge Management Portal</div>
                            </Col>
                        </Row>
                        <Row className="justify-content-center search-input-row">
                       <Col sm={6} className="mb-3">
                                <Form onSubmit={this.onSearchBtnClick} inline>
                                <Autosuggest ref={autosuggest => {
                                    if (autosuggest !== null) {
                                        this.input = autosuggest.input
                                    }
                                    }} suggestions={suggestions} onSuggestionSelected={this.onSuggestionSelected} shouldRenderSuggestions={this.shouldRenderSuggestions} onSuggestionsFetchRequested={this.onSuggestionsFetchRequested} onSuggestionsClearRequested={this.onSuggestionsClearRequested} getSuggestionValue={this.getSuggestionValue} renderSuggestion={this.renderSuggestion} inputProps={inputProps} />
                                    <button type="submit" className="btn search-btn"><FontAwesome className="fa fa-search" name="fa-search" title="Search"/></button>
                                </Form>
                                { this.state.showTrendingSearch && 
                                    <Row className="query-row">
                                        <div className="vertical-line"></div>
                                        <Col className="query-col col-sm-4">
                                        <div className="trend-serach">Trending Searches :</div>
                                        {
                                            self.state.trending_queries.map(function(query, index){
                                                if(query.length > 1){
                                                    return (<div><Label className="trend-queries" title={query} onClick={e=>self.onTrendingSearchClick(query)}>
                                                        { query.length > 20 ? query.substring(0, 20) + '...' :  query}</Label></div>)
                                                }
                                            })
                                        }
                                        </Col>
                                        <div className="vertical-line-1"></div>
                                            <Col className=" query-col-2 col-sm-4">
                                            <div className="trend-serach">Topics :</div>
                                            {
                                                self.state.trending_topics.map(function(topic, index){
                                                    if(topic.length > 1){
                                                        return (<div><Label className="trend-queries" title={topic} onClick={e=>self.onTrendingSearchClick(topic)}>
                                                            { topic.length > 22 ? topic.substring(0, 22) + '...' :  topic}</Label></div>)
                                                    }
                                                })
                                            }
                                            </Col>
                                        <div className="vertical-line-2"></div>
                                        <Col className="query-col-1 col-sm-4">
                                        <div className="trend-serach">Recently Added :</div>
                                        {
                                            self.state.trending_documents.map(function(doc, index){
                                                if(doc){
                                                    return (<div><Label className="trend-queries" onClick={e=>self.onTrendingSearchClick(doc.title)} title={doc.title}>
                                                        { doc.title.length > 20 ? doc.title.substring(0, 20) + '...' :  doc.title }</Label></div>)
                                                }
                                            })
                                        }
                                        </Col>
                                        <div className="vertical-line-3"></div>
                                    </Row>
                                }  
                            </Col>
                            { (this.state.showFilter && isValid && !this.state.error) && 
                            <Col>
                                <div className="filter-div"><span style={{padding:"10px"},{color:'grey'}}>Filter by :</span>
                                    <button type="button" value="all" className={this.isActive('all')} onClick={e=>this.handleFilter("all")}>All</button>
                                    <button type="button" value="30_days" className={this.isActive('30_days')} onClick={e=>this.handleFilter("30_days")}>30 Days</button>
                                    <button type="button" value="12_months" className={this.isActive('12_months')} onClick={e=>this.handleFilter("12_months")}>12 Months</button>
                                    <button type="button" value="3_years" className={this.isActive('3_years')} onClick={e=>this.handleFilter("3_years")}>3 Years</button>
                                </div>  
                            </Col>}
                        </Row>
                        { (this.state.showFilter && isValid && !this.state.error) && 
                        <Row>
                            <Col>
                                <div id="feedback">
                                    <a href="#" onClick={this.showModal}><span style={{padding:"12px"}}><img id="svg-img" src={svgImg} /></span> Feedback </a>
                                   
                                </div>
                            </Col>
                        </Row>
                        }
                        <Form inline>
                            <Modal className="reveal-modal" size="md" show={this.state.showFeedbackModal} onHide={this.closeFeedbackModal}>
                                <Modal.Header closeButton>
                                    <Modal.Title className="title-feedback">Feedback</Modal.Title>
                                </Modal.Header>
                                    <Modal.Body>
                                        <div className="feedback-text">Your feedback is valuable</div>
                                        <div style={{padding:"5px", paddingTop:"5px"}}>Rating :</div>
                                        <div style={{paddingLeft:"5px"}}>
                                            <StarRatings
                                                rating={this.state.rating}
                                                starRatedColor="#FFC107"
                                                changeRating={this.changeRating}
                                                numberOfStars={5}
                                                name='rating'
                                                starDimension="25px"
                                                starHoverColor="#FFC107"
                                            />
                                        </div>  
                                        <div style={{padding:"5px", paddingTop:"25px"}}>What would you like to share with us?</div>
                                        <div style={{padding:"5px" , paddingTop:"5px"}}><textarea style={{paddingLeft:"10px", paddingTop:"3px"}} className="form-control" rows="3" cols="40"  onChange={this.handleFeedbackChange} placeholder="Write here"></textarea></div>
                                        <div><Button size="sm" className="btn feedback-btn" variant="primary" onClick={this.onSubmitFeedback} disabled = { !this.state.rating && !this.state.feedback }>Submit</Button></div>
                                    </Modal.Body> 
                            </Modal>  
                         </Form>         
                    </Container>
                </section>
                <Loader spinner = {this.state.loading}/>
                {showSearchResult}
            </div > 
        )
    }
}
export default Searchbox
