import { userLogin, userRegister } from "../utils/azure.js";

import createHttpError from "http-errors";
import env from "../utils/validateEnv.js";
import express from "express";
import jwt from "jsonwebtoken";
import { requiresAuth } from "../middleware/requiresAuth.js";

const router = express.Router();
const jwtSecret = env.JWT_SECRET;

const jwtCookieOptions = {
    sameSite: "strict",
    httpOnly: true,
    signed: true,
};

const signJwt = (id) => {
    return jwt.sign({ id }, jwtSecret, { expiresIn: "1d" });
};

router.post("/login", (req, res, next) => {
    // check if body contains username and password
    if (!req.body.username || !req.body.password) {
        throw createHttpError(400, "Missing username or password");
    }
    const { username, password } = req.body;
    console.log(req.body);

    // send username and password to database
    userLogin(username, password)
        .then((response) => {
            console.log(response);

            // set jwt token
            res.cookie("token", signJwt(response.id), jwtCookieOptions);

            // send user data
            res.status(200).json({
                user: {
                    id: response.id,
                    username: response.username,
                },
            });
        })
        .catch((error) => {
            console.log(error);
            // check unauthorized
            if (error.response.status === 401) {
                next(createHttpError(401, "Incorrect password"));
            } else if (error.response.status === 404) {
                next(createHttpError(404, "Username not found"));
            } else if (error.response.status === 400) {
                next(createHttpError(400, "Missing username or password"));
            } else {
                next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

router.post("/register", (req, res, next) => {
    // check if body contains username and password
    if (!req.body.username || !req.body.password) {
        throw createHttpError(400, "Missing username or password");
    }
    const { username, password } = req.body;
    console.log(req.body);

    // send username and password to database
    userRegister(username, password)
        .then((response) => {
            console.log(response);

            // set jwt token
            res.cookie("token", signJwt(response.id), jwtCookieOptions);

            // send user data
            res.status(200).json({
                user: {
                    id: response.id,
                    username: response.username,
                },
            });
        })
        .catch((error) => {
            console.log(error);
            // check unauthorized
            if (error.response.status === 400) {
                next(
                    createHttpError(400, "Missing/invalid username or password")
                );
            } else if (error.response.status === 409) {
                next(createHttpError(409, "Username already exists"));
            } else {
                next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

router.get("/authenticated", requiresAuth, (req, res, next) => {
    res.send({
        message: "Authenticated! User id:" + req.user.id,
    });
});

router.post("/logout", (req, res, next) => {
    // Clear the token cookie
    res.clearCookie("token", {
        sameSite: "strict",
        httpOnly: true,
        signed: true,
    });
    res.status(204).send();
});

export default router;
