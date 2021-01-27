import React, { Component } from 'react';
import axios from 'axios';
import './SearchResultItem.scss';
import FontAwesome from 'react-fontawesome';
import { Modal, Row, Col, ButtonToolbar, Button, Form } from 'react-bootstrap';
import { Markup } from 'interweave';
import { API_ROOT } from '../../../../Common/api-config';
import ImageGallery from 'react-image-gallery';
import ToggleDisplay from 'react-toggle-display';
import { toast } from 'react-toastify';
import Slider from 'react-rangeslider';
import downloadImage from '../../../../assets/images/download-file1.png';
import likeImg from '../../../../assets/images/thumbs-up.png';
import dislikeImg from '../../../../assets/images/thumbs-down.png';
import likeImgFill from '../../../../assets/images/thumbs-up-fill.png';
import dislikeImgFill from '../../../../assets/images/thumbs-down-fill.png';
import doubledownImg from '../../../../assets/images/double-down.png';
import {Animated} from "react-animated-css";
import '../../../../Common/Common.scss';

var self;

class SearchResultItem extends Component {
    constructor(props) {
        super(props);
        this.state = {
            showOccurencesModal: false,
            commentValue: '',
            fileData: {
                name: '',
                occurrences: []
            },
            showIndex: true,
            showBullets: true,
            infinite: true,
            showThumbnails: false,
            showNav: true,
            isRTL: false,
            slideDuration: 450,
            slideInterval: 3000,
            slideOnThumbnailOver: false,
            showFullscreenButton: false,
            showGalleryFullscreenButton: false,
            isShowRatingsCheck: props.props.isShowRatingsCheck,
            indexSeparator: ' of ',
            images: [],
            values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            sliderData: [],
            value: 0,
            likes_count: props.props.likes_count,
            dislikes_count: props.props.dislikes_count,
            self_liked: (props.props.result.liked_status)?props.props.result.liked_status: false,
            self_disliked: (props.props.result.disliked_status)?props.props.result.disliked_status: false,
            notShowRecord:(props.props.result.notShow)?props.props.result.notShow: false,
            searchKey:"",
            isFeedbackActive:true,
            showImgModal : false,
            imgLg:'',
            showModalLoader: false
        }
        self = this;
    }

    componentDidMount(){
        if(this.refs.resultRef0){
            this.refs.resultRef0.focus();
       } 
      }

    componentWillReceiveProps(nextProps) {
        this.setState({ isShowRatingsCheck: nextProps.props.isShowRatingsCheck,
        notShowRecord:  (nextProps.props.result.notShow)?nextProps.props.result.notShow: false,
        values: nextProps.props.sliderValues,
        likes_count: nextProps.props.likes_count,
        dislikes_count: nextProps.props.dislikes_count,
        self_liked: nextProps.props.liked_status,
        self_disliked: nextProps.props.disliked_status,
        searchKey: nextProps.props.searchKey,
        session:nextProps.props.session,
        showSlider:nextProps.props.showSlider
    });
    }

    //handler for logging download details
    downloadLog = (file, index) => {
        let downloadLogArray = {
            doc_id: file.doc_id,
            search_query: this.props.props.searchKey,
            searched_result_index: index + 1 + ((this.props.props.currentPageNo-1)*10)
        }

        axios.post(API_ROOT + '/log_event_file_download', downloadLogArray)
            .then(response => {
                console.log(response);
            })
            .catch(error => {
                console.log(error);
            })
    }

    //showOccurencesModal handler
    showAddtionalInfo = (result) => {
        const data = Object.assign({}, result);
        this.setState({
            showModalLoader : true
        });
        axios.post(API_ROOT + '/preview', { doc_id: result.doc_id })
            .then(response => {
                if (response.data.slides) {
                    let images = [];
                    response.data.slides.map((slide, index) => {
                        images.push({ 'original': slide.thumbnail_large})
                    })
                    this.setState({
                        fileData: data,
                        images: images,
                        fileName: data.file_name,
                    });
                    this.setState({showOccurencesModal: true})   
                    setTimeout(this.setState({
                        showModalLoader : false
                    }), 200)
                    
                } else {
                    toast("No preview available.", {
                        position: "bottom-right",
                        autoClose: 4000,
                        hideProgressBar: true,
                        closeOnClick: false,
                        pauseOnHover: false,
                        draggable: false,
                        pauseOnFocusLoss: false
                    });
                }
            })
            .catch(error => {
                console.log(error)
            })
    }

    //Modal close handler
    closeHandler = () => {
        this.setState({
            showOccurencesModal: false
        });

    }

    //Feedback handler
    feedbackBtnClicked = (event, feedback, doc_id) => {
        event.preventDefault();
        this.setState({
            isFeedbackActive : false
        });

        setTimeout(() => {
            this.setState({
                isFeedbackActive : true
            });
        }, 4000);

        let feedbackArray = {
            feedback: feedback,
            docId: doc_id,
            searchQuery: this.props.props.searchKey,
            DateTime: new Date()
        }


       if(this.state.isFeedbackActive){ 
           axios.post(API_ROOT + '/feedback', feedbackArray)
            .then(response => {
                if (response.data.liked_status === true) {
                    this.setState({
                        likes_count: response.data.num_likes,
                        dislikes_count: response.data.num_dislikes,
                        self_liked: true,
                        self_disliked: false
                    },()=>{
                        self.props.props.updateSearchResult(doc_id, response.data.num_likes, response.data.num_dislikes,true)
                    })
                }
                else {
                    this.setState({
                        dislikes_count: response.data.num_dislikes,
                        likes_count: response.data.num_likes,
                        self_liked: false,
                        self_disliked: true
                    },()=>{
                        self.props.props.updateSearchResult(doc_id, response.data.num_likes, response.data.num_dislikes,false)
                    })
                }
                toast("You have successfully submitted your feedback!", {
                    position: "bottom-right",
                    autoClose: 4000,
                    hideProgressBar: false,
                    closeOnClick: false,
                    pauseOnHover: false,
                    draggable: false
                });
            })
            .catch(error => {
                console.log(error);
            })
       }
        this.closeHandler();
    }

    //Slider value change handler
    onChangeSlider = (value, i, result) => {
        let newVal = { ...this.state.values };
        newVal[i] = value;
        this.setState({
            values: newVal
        });
        this.props.props.updateSliderList(i, value);
        this.props.props.updateSliderDataList(i, value, result);
    }

    handleChange = value => {
        this.setState({
            value: value
        })
    };

    // image click handler on preview pop up.
    previewImgClick = (e, index) => {
        var clickedIndx = index-1;
        this.refs.imgGallery.slideToIndex(clickedIndx);
    }

    showMore = (arrToShow, parentIdx) =>{
        let btnId = "BTN"+parentIdx;
        
        if(document.getElementById(btnId).innerText === "Show Less"){
            let image = document.createElement('img');
            image.src = doubledownImg
            document.getElementById(btnId).innerHTML = 'Show More ' + arrToShow.length + ' result ';
            document.getElementById(btnId).appendChild(image)
        } else {
            document.getElementById(btnId).innerText = "Show Less";
        }
        arrToShow.map((ele) => {
            let id = "PPT"+ele;
            if(document.getElementById(id).style.display == "none"){
                document.getElementById(id).setAttribute("style","display:'';padding-left: 40px");
                

            } else {
                document.getElementById(id).setAttribute("style","display:none;padding-left: 0px");
            }
        })
    }
    
    updateSliderValues = () => {
        this.setState({
            values: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        });
    }


    showImage = (imgLg)=>{
        this.setState({
            showImgModal : true,
            imgLg:imgLg
        })
    }

    closeImage = ()=>{
        this.setState({
            showImgModal : false
        })
    }

    render() {
        toast.configure();

        let context = this.props.props.context;
        if (context !== "") {
            context = context + "...";
        }
        let title = this.props.props.title;
        let result = this.props.props.result;
        let index = this.props.props.index;
        //let img = this.props.props.img;

        let thumbnailListContent = null;
        let occurrencesList = null;
        let thumbnails = [];
        const labels = {
            0: 'Na',
            1: '1',
            2: '2',
            3: '3',
            4: '4',
            5: '5'
        };

        let img;
       // let thumbnailsImg = [];
        let thumb = [];
        
        result.occurrences.map((occurence,index) => {
            if (thumb.indexOf(occurence.thumbnail_small) == -1)
            thumb.push(
                {
                'imgSm':occurence.thumbnail_small,
                'imgLg':occurence.thumbnail_large
                }
            )
        });

        thumb = thumb.slice(0, 3);
        const thumbnailsImg = thumb.filter(function({imgSm, imgLg}) {
            const key =`${imgSm}${imgLg}`;
            return !this.has(key) && this.add(key);
          }, new Set);
       
        let thumbnailList = thumbnailsImg.map((thumbnail, index) => {
            return <img className="mr-2 cust-img" src={thumbnail.imgSm} key={index + Math.random()} width="190px" height="107px" onClick={()=>this.showImage(thumbnail.imgLg)}/>
        });
        img = (
            <span class="img-space">
                {thumbnailList}
            </span>
        )

        result.occurrences.map((occurence, index) => {
            if (occurence.content !== "") {
                const found = thumbnails.some(el => el.img === occurence.thumbnail_small);
                if (!found) {
                    thumbnails.push({
                        'img': occurence.thumbnail_small,
                        'slideNo': occurence.page_no
                    });
                }
            }
        });

        thumbnailListContent = thumbnails.map((thumbnail, index) => {
            return <img className="ml-2 mb-1 mr-2 img-cls" src={thumbnail.img} key={index + Math.random()} width="190px" height="px" onClick={(e) => this.previewImgClick(e, thumbnail.slideNo)} />
        });

        let divHt = (thumbnailListContent.length * 112) + (thumbnailListContent.length * 6);
        if (thumbnailListContent.length !== 0) {    
            occurrencesList = <Col sm={3} className="occurence-div"><div className="thumbnail-list1" style={{ height: divHt }} >{thumbnailListContent}</div></Col>
        } else {
            let divHt = (thumbnailListContent.length * 112) + (thumbnailListContent.length * 6);
            occurrencesList = <Col sm={3} className="occurence-div"><div className="thumbnail-list1" style={{ height: divHt }} ></div></Col>
        }


        let divId = "PPT"+this.props.props.index;
        let resultRef = "";
        if(divId == "PPT0"){
             resultRef = "resultRef"+this.props.props.index;
        }
        let createdBy = result.created_by;
        createdBy = createdBy.split(";").join(' ; ');
       
      

        return (
            <div tabIndex={0} className="search-result-focus" ref={resultRef} style={{display: (this.state.notShowRecord)?"none":"", paddingLeft: (this.state.notShowRecord)?"0px !important":""}} id = {divId}>
                <Row className="search-result-file">
                    <Col sm={5}>
                        <Row className="file-info">
                            <Col sm={8} className="p-0">
                                <div className="file-name float-left mb-2">{title}</div>
                            </Col>
                            <Col sm={4} className="p-0">
                                <span className="feedback-count mr-2">{this.state.likes_count}</span>
                                {
                                    (!this.state.self_liked)?
                                        <img src={likeImg} className="mr-4 pointer" title="Like" width="15" height="15" alt="Like Files" onClick={(e) => this.feedbackBtnClicked(e, "1", result.doc_id)}/>
                                    : <img src={likeImgFill} className="mr-4" title="Like" width="15" height="15" alt="Like Files"/>
                                }
                                <span className="feedback-count">{this.state.dislikes_count}</span>
                                {
                                    (!this.state.self_disliked)?
                                        <img src={dislikeImg} className="mr-4 dislike-btn pointer" title="Dislike" width="15" height="15" alt="Dislike File" onClick={(e) => this.feedbackBtnClicked(e, "-1", result.doc_id)}/>
                                    : <img src={dislikeImgFill} className="mr-4 dislike-btn" title="Dislike" width="15" height="15" alt="Dislike Files"/>
                                }
                            </Col>
                        </Row>
                        <Row className="file-info">
                            <div className="text-left file-context">
                                <Markup content={context} />
                            </div>
                        </Row>
                        <Row className="file-info">
                            <Col className="text-left search-result-metadata">
                                <div>Created By :&nbsp;<span className="created-by-result" title={createdBy}>{ result.created_by.length > 17 ? createdBy.substring(0, 17) + '...' :  createdBy }</span> </div>
                                <div>Modified By :&nbsp;<span className="created-by-result" title={result.modified_by}>{ result.modified_by.length > 17 ? result.modified_by.substring(0, 17) + '...' : result.modified_by }</span> </div>
                                <div style={{paddingTop: "8px"}}>
                                    <span >No. of Downloads : </span>
                                    <span>{result.num_downloads}</span>
                                </div>
                            </Col>
                            <Col className="text-left search-result-metadata">
                                <div>Created Date :&nbsp; {new Date(result.created_date).toLocaleString()} </div>
                                <div>Last Modified :&nbsp; {new Date(result.modified_date).toLocaleString()} </div>
                            </Col>
                        </Row>
                        <Row className="file-info">
                            <Col sm={5} div className="text-left pl-0">
                                <ButtonToolbar className="mt-2">
                                    <Button onClick={() => this.showAddtionalInfo(result)} variant="outline-primary preview-btn">Preview</Button>
                                     <Button tabIndex="1" id="download-btn-click" variant="outline-primary download-btn ml-2">
                                        <a tabIndex="0" href={result.url} onClick={() => this.downloadLog(result, index)} target="_blank" rel="noopener noreferrer" className="download-link"><p className="dwnTxt">Download</p></a>
                                    </Button>  
                                   
                                </ButtonToolbar>
                            </Col>
                            <Col sm={7}>
                                    <Form>
                                        <Row>
                                        <Col sm={1}></Col>
                                            { this.props.props.showSlider &&
                                            <Col className="col-space" sm={10}>
                                                <Slider
                                                    value={this.state.values[index] || 0}
                                                    min={0}
                                                    max={5}
                                                    labels={labels}
                                                    orientation="horizontal"
                                                    onChange={(e) => this.onChangeSlider(e, index, result)}
                                                    className="mt-3"
                                                />
                                            </Col>
                                            }
                                        </Row>
                                    </Form>
                            </Col>
                        </Row>
                        {
                            (this.props.props.result.posIdx)?
                            <Row className="file-info">
                            <Col sm={5} div className="text-left pl-0">
                                <ButtonToolbar className="mt-2">
                                    <a className="accordian-link" id = {"BTN" + this.props.props.index} onClick={() => this.showMore(this.props.props.result.posIdx, this.props.props.index)} >Show More {this.props.props.result.posIdx.length} result <img src={doubledownImg} className="ml-2" width="12" height="12" alt="DoubleDown"/></a>
                                </ButtonToolbar>
                            </Col>
                            </Row>:""
                        }
                        
                    </Col>
                    <Col sm={7}>
                        <div className="occurrences-thumbnail">
                            {img}
                        </div>
                    </Col>
                </Row>
                
                {/* Info Modal */}
                <Modal size="lg" centered show={this.state.showOccurencesModal} onHide={this.closeHandler} id="occurences-modal">
                    <div>
                        <a href="#" title="Close" className="close-button mt-2 mr-2" onClick={this.closeHandler}></a>
                        <h5 className="title-preview">{title}</h5>
                    </div>
                    <div className="file-occurence">
                        <div className="file-download">
                            <p className="title-fileName">{this.state.fileName}</p>
                            <a className="float-right" href={this.state.fileData.url} 
                                onClick={() => this.downloadLog(result, index)} target="_blank" 
                                rel="noopener noreferrer">
                                <img src={downloadImage} width="15" height="15" alt="user profile" className="download-img" style={{"float":"right"}} />
                            </a>
                            <p className="download-text">Download file from Egnyte</p>
                        </div>
                        <div className="occurences-text">
                            <h5 className="title-occurences">Occurences</h5>
                        </div>
                    </div>
                    <Modal.Body>
                    <Row>
                            <Col sm={9} style = { {border: '1px', position: 'relative'} }>
                            { this.state.showModalLoader ? 
                                     <div style={{marginTop:"150px"}} className="loader"></div> :
                                     <ImageGallery ref="imgGallery"
                                     items={this.state.images}
                                     lazyLoad={false}
                                     infinite={this.state.infinite}
                                     showBullets={this.state.showBullets}
                                     showThumbnails={this.state.showThumbnails}
                                     showIndex={this.state.showIndex}
                                     showNav={this.state.showNav}
                                     isRTL={this.state.isRTL}
                                     slideDuration={parseInt(this.state.slideDuration)}
                                     slideInterval={parseInt(this.state.slideInterval)}
                                     slideOnThumbnailOver={this.state.slideOnThumbnailOver}
                                     indexSeparator={this.state.indexSeparator}
                                     showFullscreenButton={this.state.showFullscreenButton && this.state.showGalleryFullscreenButton} />
                                }
                               <Row className="file-metadata mt-5" style={{"margin-left":"0px", position: 'absolute', bottom: '0'}}>
                                    <Col>
                                        <Row className="justify-content-start mr-2">
                                            <span title={createdBy}>Created By : &nbsp; { result.created_by.length > 17 ? createdBy.substring(0, 17) + '...' :  createdBy }</span>
                                        </Row>
                                        <Row className="justify-content-start mr-2">
                                            <span>Last Modified :&nbsp; {new Date(this.state.fileData.modified_date).toLocaleString()}</span>
                                        </Row>
                                    </Col>
                                    <Col style={ {width: '9cm'} }></Col>
                                    <Col className="col col-lg-3">
                                    <Row>No. of Downloads : {this.state.fileData.num_downloads}</Row>
                                    </Col>
                                </Row>
                            </Col>
                            {occurrencesList}
                        </Row> 
                    </Modal.Body>
                </Modal>
                <Modal tabindex="-1" size="lg" show={this.state.showImgModal} onHide={this.closeImage}>
                    <div>
                        <a href="#" title="Close" className="close-button mt-2 mr-2" onClick={this.closeImage}></a>
                        <h5 className="title-preview">Preview</h5>
                    </div>
                   <Modal.Body className="modal-style">
                        <img src={this.state.imgLg}/>
                    </Modal.Body> 
                </Modal>
            </div>
        );
    }
}

export default SearchResultItem;