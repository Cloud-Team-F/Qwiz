import createHttpError from "http-errors";
import express from "express";
import { quizJoin } from "../utils/azure.js";
import { requiresAuth } from "../middleware/requiresAuth.js";

const router = express.Router();

router.post("/join/:inviteCode", requiresAuth, async (req, res, next) => {
    quizJoin(req.params.inviteCode, req.user.id)
        .then((response) => {
            res.json(response);
        })
        .catch((error) => {
            console.log(error);

            if (!error.response) {
                return next(createHttpError(500, "An unknown error occurred"));
            } else if (error.response.status == 400) {
                return next(createHttpError(400, error.response.data.error));
            } else if (error.response.status == 404) {
                return next(createHttpError(404, error.response.data.error));
            } else {
                return next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

export default router;
