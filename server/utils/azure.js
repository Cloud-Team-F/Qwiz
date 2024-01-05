import axios from "axios";
import env from "./validateEnv.js";

function fetchHelper(
    endpoint,
    method,
    body = null,
    queryParams = {},
    headers = { "Content-Type": "application/json" },
    responseType = "json"
) {
    const queryString = new URLSearchParams(queryParams).toString();
    const functionToken = env.AZURE_FUNCTION_TOKEN;
    const url =
        env.AZURE_FUNCTION_URL +
        endpoint +
        "?" +
        (functionToken ? `code=${functionToken}` : "") +
        (queryString ? `&${queryString}` : "");

    console.log("Request to:", url);
    return axios({
        method: method,
        url: url,
        data: body,
        headers: headers,
        responseType: responseType,
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

export function quizDelete(quiz_id, user_id) {
    return fetchHelper("/quiz_delete", "POST", {
        quiz_id,
        user_id,
    });
}

export function quizLeave(quiz_id, user_id) {
    return fetchHelper("/quiz_leave", "POST", {
        quiz_id,
        user_id,
    });
}

export function quizJoin(invite_code, user_id) {
    return fetchHelper("/quiz_join", "POST", {
        invite_code,
        user_id,
    });
}

export function quizAnswer(quiz_id, user_id, answers) {
    return fetchHelper("/answer_quiz", "POST", {
        quiz_id,
        user_id,
        answers,
    });
}

export function textToSpeech(text) {
    return fetchHelper("/convert_to_speech", "POST", { text }, {}, {}, "arraybuffer");
}
