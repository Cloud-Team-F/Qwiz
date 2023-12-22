import createHttpError from "http-errors";
import env from "../utils/validateEnv.js";
import jwt from "jsonwebtoken";

const jwtSecret = env.JWT_SECRET;

export function requiresAuth(req, res, next) {
    // get jwt cookie
    const token = req.signedCookies.token;

    // check if jwt is valid
    try {
        jwt.verify(token, jwtSecret);

        // save user data to req.user
        req.user = jwt.decode(token);
    } catch (error) {
        next(createHttpError(401, "Unauthorized"));
        return;
    }
    next();
}
