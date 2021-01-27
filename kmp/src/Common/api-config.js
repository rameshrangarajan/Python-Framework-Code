let baseUrl;

const hostname = window.location.origin;

// if (hostname == "http://localhost:8080"){
//     baseUrl = "http://10.21.6.44:8000"; 
// }
// else{
    baseUrl = hostname;
// }

export const API_ROOT = `${baseUrl}`