import axios from "axios";
import env from "./validateEnv.js";

function fetchHelper(endpoint, method, body = null) {
    return axios({
        method: method,
        url:
            env.AZURE_FUNCTION_URL +
            endpoint +
            "?code=" +
            env.AZURE_FUNCTION_TOKEN,
        data: body,
        headers: { "Content-Type": "application/json" },
    }).then((response) => response.data);
}

export function userLogin(username, password) {
    return fetchHelper("/user_login", "POST", { username, password });
}

export function userRegister(username, password) {
    return fetchHelper("/user_register", "POST", { username, password });
}