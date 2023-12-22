import axios from "axios";
import env from "./validateEnv.js";

function fetchHelper(endpoint, method, body = null, queryParams = {}) {
    const queryString = new URLSearchParams(queryParams).toString();
    const url =
        env.AZURE_FUNCTION_URL +
        endpoint +
        "?code=" +
        env.AZURE_FUNCTION_TOKEN +
        (queryString ? `&${queryString}` : "");

    return axios({
        method: method,
        url: url,
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

export function userGet(id) {
    return fetchHelper("/user_get", "GET", null, { id });
}
