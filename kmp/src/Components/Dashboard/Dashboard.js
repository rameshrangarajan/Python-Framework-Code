import React, { Component } from 'react';
import Card from 'react-bootstrap/Card';
import './Dashboard.scss';
import { Label } from 'semantic-ui-react'
import { API_ROOT } from '../../Common/api-config'
import axios from 'axios';
import { Container, Row, Col, Form, Button } from 'react-bootstrap';
import BootstrapTable from 'react-bootstrap-table-next';
import { func } from 'prop-types';
var self;
class Dashboard extends Component {
    constructor(props) {
        super(props);
        let tempArr = [];
        for(let i=0;i<6;i++){
            tempArr.push({
                'period': '',
                'users': '',
                'queries': '',
                'downloads': '',
                'downloads_on_first_page': '',
                'ratings': '',
                'avg_query_time': '',
                'accepted_suggestions':'',
            })
        }
        self = this;
        this.state = {
            data: tempArr,
            recent_queries:[],
            trending_queries:[],
            rows: [{
                key: "today",
                value: "Today :"
            }, {
                key: "this_week",
                value: "This Week :"
            },
            {
                key: "last_week",
                value: "Last Week :"
            }, {
                key: "this_month",
                value: "This Month :"
            }, {
                key: "last_month",
                value: "Last Month :"
            }, {
                key: "this_year",
                value: "This Year :"
            }],
            columns: [
                {
                    dataField: "period",
                    text: "",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                      }
                },
                {
                    dataField: "users",
                    text: "No. of Users",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                    },
                    formatter: self.colorFormatter
                },
                {
                    dataField: "queries",
                    text: "No. of Queries",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                    },
                    formatter: self.colorFormatter
                },
                {
                    dataField: "downloads",
                    text: "No. of Downloads",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                    },
                    formatter: self.colorFormatter
                },
                {
                    dataField: "downloads_on_first_page",
                    text: "Downloads on 1st Page",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                    },
                    formatter: self.colorFormatter
                },
                {
                    dataField: "ratings",
                    text: "Ratings Received",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                    },
                    formatter: self.colorFormatter
                },
                {
                    dataField: "avg_query_time",
                    text: "Avg. Query Time (s)",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                    },
                    formatter: self.colorFormatter
                },
                {
                    dataField: "accepted_suggestions",
                    text: "No. of accepted suggestions",
                    headerStyle: (colum, colIndex) => {
                        return { width: '120px', textAlign: 'center' };
                    },
                    formatter: self.colorFormatter
                }
            ]
        }
        //self = this;
    }

    componentWillMount() {
        this.getData();
        self.getQueries();
    }

    refreshData(){
        self.getData();
        self.getQueries();
    }

    getData = () => {
        let usageResult = [];
        let promise = Promise.all([this.getTodayUsageMatrics, this.getThisWeekUsageMatrics, this.getLastWeekUsageMatrics, this.getThisMonthUsageMatrics, this.getLastMonthUsageMatrics, this.getThisYearUsageMatrics])
            .then(result => {
                console.log("result", result);
                if (result) {
                    result.forEach((day, index) => {
                        const a = ['period', 'users', 'queries', 'downloads', 'downloads', 'downloads_on_first_page', 'ratings', 'avg_query_time', 'accepted_suggestions'];
                        const keys = a.reduce((val, ind) => {
                            if (ind === "period") {
                                let rowData = [...self.state.rows];
                                let nameofRow = rowData.find(o => o.key === day[ind].value);
                                val[ind] = nameofRow.value;
                            } else {
                                val[ind] = day[ind].value+"+"+day[ind].trend;
                            }
                            return val;
                        }, {});
                        usageResult.push(keys);
                    });
                    this.setState({
                        data: usageResult
                    });
                }

            })
            .catch(error => {
                console.log(error)
            })
    }

    getQueries(){
        axios.post(API_ROOT + '/get_queries_metrics', '', { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            if (response.data.recent_queries || response.data.trending_queries) { //If status key is present (show error)
                this.setState({
                    recent_queries : (response.data.recent_queries)?response.data.recent_queries:[],
                    trending_queries : (response.data.trending_queries)?response.data.trending_queries:[]
                })
            }
        })
        .catch(error => {
            console.log(error);
        })  
    }

    getTodayUsageMatrics = axios.post(API_ROOT + '/get_usage_metrics', { 'period': 'today' }, { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            // console.log(response.data);
            return response.data;
        })
        .catch(error => {
            console.log(error)
        })


    getThisWeekUsageMatrics = axios.post(API_ROOT + '/get_usage_metrics', { 'period': 'this_week' }, { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            //console.log(response.data);
            return response.data;
        })
        .catch(error => {
            console.log(error)
        })

    getLastWeekUsageMatrics = axios.post(API_ROOT + '/get_usage_metrics', { 'period': 'last_week' }, { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            //console.log(response.data);
            return response.data;
        })
        .catch(error => {
            console.log(error)
        })

    getThisMonthUsageMatrics = axios.post(API_ROOT + '/get_usage_metrics', { 'period': 'this_month' }, { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            //console.log(response.data);
            return response.data;
        })
        .catch(error => {
            console.log(error)
        })

    getLastMonthUsageMatrics = axios.post(API_ROOT + '/get_usage_metrics', { 'period': 'last_month' }, { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            //console.log(response.data);
            return response.data;
        })
        .catch(error => {
            console.log(error)
        })

    getThisYearUsageMatrics = axios.post(API_ROOT + '/get_usage_metrics', { 'period': 'this_year' }, { headers: { 'Content-Type': 'application/json' } })
        .then(response => {
            //console.log(response.data);
            return response.data;
        })
        .catch(error => {
            console.log(error)
        })


    rowClasses = '';
    colorFormatter(cell, row) {
        let val = cell.split('+');
        if (cell) {            
            let color = "";
            if(val[1] == 1){
                color = "#6EB31A";
            }
            if(val[1] == 0){
                color = "black";
            }
            if(val[1] == -1){
                color = "red";
            }
          return (
            <span>
              <strong style={{ color: color}}>{val[0]}</strong>
            </span>
          );
        }
      
        return (
          <span>{val[0]}</span>
        );
    }
    render() {
        if(document.getElementsByClassName('header')[0]){
            document.getElementsByClassName("container-box")[0].setAttribute("style", "top: 13%;");
            document.getElementsByClassName("header")[0].setAttribute("style", "background-color: #17a1cc");
        }
        
        return (
            <div>
                <div className="dashboard-title">
                    Dashboard
                    {/* <Button className="pull-right refreshBtn"
                        variant="primary"
                        onClick={self.refreshData}
                    >
                        Refresh Data
                    </Button> */}
               </div>
               <div className="tableClass">
                <BootstrapTable classes="table-cust table-data" keyField='id' data={this.state.data} columns={this.state.columns} headerClasses="table-head" />
                </div>
                <div className="container-fluid">
                    <div className="queryClass">
                        <Row>
                            <div className="tagClass">
                                <Card className="card-details">
                                    <Card.Body>
                                        <Card.Title className="card-title">Recent Queries</Card.Title>
                                        <Card.Text>
                                        {
                                            self.state.recent_queries.map(function(m, index){
                                                return <Label>{m}</Label>
                                            })
                                        }
                                        </Card.Text>
                                    </Card.Body>
                                </Card>
                            </div>
                            <div className="tagClass">
                                <Card className="card-details-trend">
                                    <Card.Body>
                                        <Card.Title className="card-title">Trending Queries</Card.Title>
                                        <Card.Text>
                                        {
                                            self.state.trending_queries.map(function(m, index){
                                                return <Label>{m}</Label>
                                            })
                                        }
                                        </Card.Text>
                                    </Card.Body>
                                </Card>
                            </div>
                        </Row>
                    </div>
                </div>
            </div>

        );
    }

}

export default Dashboard;