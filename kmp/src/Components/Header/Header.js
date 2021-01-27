import React, { Component } from 'react';
import logo from '../../assets/images/logo.png';
import userProfile from '../../assets/images/userProfile.png'
import { Navbar } from 'react-bootstrap';
import FontAwesome from 'react-fontawesome';
import Cookies from 'js-cookie';
import jwt_decode from 'jwt-decode';
import Dropdown, { DropdownTrigger, DropdownContent } from 'react-simple-dropdown';


class Header extends Component {
    constructor(props) {
        super();
        if (Cookies.get('user_name') && Cookies.get('email')) {
            this.state = {
                userData: { unique_name: Cookies.get('user_name'), emailAddress: Cookies.get('email') }
            }
        } else {
            this.state = {
                userData: { unique_name: 'Username', emailAddress: 'username@xoriant.com' }
            }
        }

    }
    render() {
        return (
            <div>
                <Navbar fixed="top" className="header p-0">
                    <Navbar.Brand className="m-0" href="/">
                        <img
                            alt=""
                            src={logo}
                            width="82"
                            height="42"
                            className="d-inline-block align-top ml-2"
                        />
                    </Navbar.Brand>
                    <Navbar.Text className="text-center w-100">
                        <span className="title m-0">Knowledge Management Portal</span>
                    </Navbar.Text>
                    <Navbar.Text className="justify-content-end">
                        <Dropdown>
                            <DropdownTrigger>
                                <img
                                    src={userProfile}
                                    className="d-inline-block align-top mr-3"
                                    width="42"
                                    height="42"
                                    alt="user profile"
                                    title="User Profile"
                                />
                            </DropdownTrigger>
                            <DropdownContent>
                                <ul>
                                    <li>
                                        <div>{this.state.userData.unique_name}</div>
                                        <div>{this.state.userData.emailAddress}</div>
                                    </li>
                                    <li className="logout">
                                        <a className="logout-link" href="/logout">Logout</a>
                                    </li>
                                </ul>
                            </DropdownContent>
                        </Dropdown>
                    </Navbar.Text>
                </Navbar>
            </div>
        )
    }
}

export default Header
