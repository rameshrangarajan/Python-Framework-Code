import React, { Component } from 'react';
import axios from 'axios';
import Autosuggest from 'react-autosuggest';
import AutosuggestHighlightMatch from 'autosuggest-highlight/umd/match';
import AutosuggestHighlightParse from 'autosuggest-highlight/umd/parse';
import FontAwesome from 'react-fontawesome';
import SearchResultTrain from './SearchResultTrain/SearchResultTrain';
import { isEmpty } from 'lodash';
import { API_ROOT } from '../../Common/api-config'
import { Container, Row, Col, Form, Button } from 'react-bootstrap';
import backgroundImage from '../../assets/images/appBackground.png';
import Switch from "react-switch";
import Loader from '../Loader/Loader';
var self;
class SearchboxTrain extends Component {

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
            loading:''
        };
        self = this;
    }

    //Search button click event function
    onSearchBtnClick = (event) => {
        event.preventDefault();
        this.input.blur()
        let value = this.state.value.trim();  //to remove white spaces
        if (!isEmpty(value)) { //If search field is not empty

            this.setState({
                page_number: 1,
                loading:true
            });
            let searchAPIData = {
                'query': this.state.value.trim(),
                'page_number': 1,
                'query_type' : 'search',
                'time_filter' : 'all'
            }
            this.refs.child.updateSliderAPIData();
            this.setState({
                isShowRatingsCheck: false
            });
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
                                showTrainingPanel: true,
                                loading:false
                                
                            })
                        })
                        this.saveToStorage(this.state.value.trim());

                    }
                })
                .catch(error => {
                    console.log(error);
                    this.setState({ loading : false});
                })
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
        let data = JSON.parse(localStorage.getItem('history'));
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
            isValid: true
        });
    };

    //Teach Autosuggest how to calculate suggestions for any given input value.
    getSuggestions = value => {
        const inputValue = value.trim().toLowerCase();
        const inputLength = inputValue.length;

        let slist = [];
        let suggestionArray = [];
        this.setState({ suggestionList: [] });
        if (inputLength >= 3) {
            return axios.post(API_ROOT + '/suggest', { 'query': value })
                .then(response => {

                    suggestionArray = response.data.related_keywords;

                    suggestionArray.map(element => {
                        slist.push({ name: element })
                    })

                    this.setState({
                        suggestionList: slist,
                        suggestions: slist
                    })

                })
                .catch(error => {
                    console.log(error)
                });
        } else {
            //this.setState({ suggestionList: [] });
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
        let endItem = Math.ceil(totalResults / 10) === currentPage ? totalResults : (startItem - 1) + 11;
        let searchResults = this.state.results.slice(startItem, endItem);

        this.setState({
            page_number: currentPage,
            searchResult: searchResults,
            isShowRatingsCheck: false
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
            'query': this.state.value,
            'page_number': currentPage,
            'query_type' : 'navigation'
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
                            loading:false
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
        self.setState({
            textVal: value
        },()=>{
            this.getSuggestions(value)
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
            if(self.state.textVal=="")
                self.recoverHistory();
        }, false);
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
        this.setState({isAnySliderValChanged: true})
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

        // This function will get called 
    // to log the details related to autosuggest usage
    onSuggestionSelection = (suggestionValue,suggestionIndex) => {
        suggestionValue = suggestionValue.trim().toLowerCase();
        let dateTime = new Date();
        let searchAPIData = {
            'search_query': this.state.value.trim(),
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
    
    render() {

        const { value, searchResult, suggestions, suggestionList, isValid, error, data, isLoaded } = this.state;

        const inputProps = {
            placeholder: 'Type a keyword here..',
            value,
            onChange: this.onChange,
            placeholder: 'Search',
            autoFocus: true
        };
        let showSearchResult = null
        if (isValid) {
            showSearchResult = (
                <div>
                    <SearchResultTrain ref="child"
                        results={searchResult}
                        data={data}
                        error={error}
                        searchKey={value}
                        pageNo={this.state.page_number}
                        pageChange={this.pageChange}
                        sliderValueLister = {this.sliderValueLister}
                        updateSearchResult = {this.updateSearchResult}/>
                </div>
            );
        } else {
            showSearchResult = (
                <div className="alert alert-danger mt-5" role="alert">Please enter a search key!</div>
            );
        }

        let trainingPanel = null;

        let submitBtn = null;

        if (this.state.isShowRatingsCheck) {
            var variant = 'secondary';

            if(this.state.isAnySliderValChanged === true) {
                variant = 'primary';
            }
            submitBtn = (<Button style = {{marginLeft : "4px"}} variant={ variant } type="submit" onClick={this.gradeSubmit} className="trainingSubBtn mr-4" disabled = { !this.state.isAnySliderValChanged }>submit</Button>)
        }

        if (this.state.showTrainingPanel === true) {
            trainingPanel = 
            <Col style = {{marginLeft: "21vw"}}>
            <Row className="justify-content-center  mb-2 ">
            <React.Fragment style = {{marginRight: "95px"}}>
            <td style = {{verticalAlign:"bottom"}}>
            <b>Train</b>
            </td>
            <span>
            <Switch className="ml-3" onChange={this.handleSwitchChange} checked={this.state.isShowRatingsCheck} />
            </span>
            </React.Fragment>
            <span style = {{width: "2cm", marginLeft: "30px", marginRight: "20px"}}>
            {submitBtn}</span>
            </Row>
            </Col>
        } else {
            trainingPanel = null;
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
                        
                            <Col sm={6}  >
                                <Form onSubmit={this.onSearchBtnClick} inline>
                                    <Autosuggest ref={autosuggest => {
                                    if (autosuggest !== null) {
                                        this.input = autosuggest.input
                                    }
                                    }} suggestions={suggestions} onSuggestionSelected={this.onSuggestionSelected} shouldRenderSuggestions={this.shouldRenderSuggestions} onSuggestionsFetchRequested={this.onSuggestionsFetchRequested} onSuggestionsClearRequested={this.onSuggestionsClearRequested} getSuggestionValue={this.getSuggestionValue} renderSuggestion={this.renderSuggestion} inputProps={inputProps} />
                                    <button type="submit" className="btn search-btn"><FontAwesome className="fa fa-search" name="fa-search" /></button>
                                </Form>
                            </Col>
                            
                            {trainingPanel}
                        </Row>
                    </Container>
                </section>
                <Loader spinner = {this.state.loading}/>
                {showSearchResult}
            </div >
        )
    }
}

export default SearchboxTrain
