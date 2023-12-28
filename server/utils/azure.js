import axios from "axios";
import env from "./validateEnv.js";

function fetchHelper(
    endpoint,
    method,
    body = null,
    queryParams = {},
    headers = { "Content-Type": "application/json" }
) {
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
        headers: headers,
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

export function quizCreate(formData, headers) {
    return fetchHelper("/upload_documents", "POST", formData, {}, headers);
}

export function quizGetAll(id) {
    return fetchHelper("/quiz_get_all", "GET", null, { id });
}

export function quizGet(quiz_id, user_id) {
    return fetchHelper("/quiz_get", "GET", null, {
        quiz_id: quiz_id,
        user_id: user_id,
    });
}
