import {
    quizAnswer,
    quizCreate,
    quizDelete,
    quizGet,
    quizGetAll,
    quizLeave,
} from "../utils/azure.js";

import FormData from "form-data";
import { WebPubSubEventHandler } from "@azure/web-pubsub-express";
import { WebPubSubServiceClient } from "@azure/web-pubsub";
import createHttpError from "http-errors";
import env from "../utils/validateEnv.js";
import express from "express";
import multer from "multer";
import { requiresAuth } from "../middleware/requiresAuth.js";

const router = express.Router();

// Multer
const upload = multer();
const supportedFileTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
];

// PubSub client
const hubName = "hub";
let serviceClient = new WebPubSubServiceClient(
    env.PUBSUB_CONNECTION_STRING,
    hubName
);

// PubSub event handler
let handler = new WebPubSubEventHandler(hubName, {
    path: "/eventhandler",
    handleConnect: (req, res) => {
        res.success({
            groups: ["system", "message"],
        });
    },
    onConnected: (req) => {
        console.log(`${req.context.userId} connected`);
    },
});

router.use(handler.getMiddleware());
router.get("/negotiate", requiresAuth, async (req, res) => {
    let options = {
        userId: req.user.id,
    };
    let token = await serviceClient.getClientAccessToken(options);
    res.status(200).json({
        url: token.url,
    });
});

router.post("/create", upload.any(), requiresAuth, async (req, res, next) => {
    // Check for missing parameters
    if (
        !req.body["quiz_name"] ||
        !req.body["num_questions"] ||
        !req.body["question_types"]
    ) {
        next(
            createHttpError(
                400,
                "Missing quiz name, number of questions, or question types"
            )
        );
        return;
    }

    // Validate quiz name
    if (req.body["quiz_name"].length < 1 || req.body["quiz_name"].length > 50) {
        next(
            createHttpError(
                400,
                "Quiz name cannot be empty and be at most 50 characters"
            )
        );
        return;
    }

    // Check there are files or content
    if (req.files.length === 0 && !req.body["content"]) {
        next(createHttpError(400, "No files or content provided"));
        return;
    }
    if (req.files.length > 3) {
        next(createHttpError(400, "Maximum 3 files allowed"));
        return;
    }

    // Create a new FormData instance
    const formData = new FormData();

    // Append text fields
    for (const key in req.body) {
        formData.append(key, req.body[key]);
    }

    // Add user id field
    formData.append("user_id", req.user.id);

    // Append files
    for (const file of req.files) {
        console.log(file.originalname);

        // Check valid file type
        if (!supportedFileTypes.includes(file.mimetype)) {
            return next(createHttpError(415, "Unsupported file type"));
        }

        formData.append("files[]", file.buffer, {
            filename: file.originalname,
            contentType: file.mimetype,
        });
    }

    // Send request to Azure Function
    quizCreate(formData, formData.getHeaders())
        .then((response) => {
            res.status(200).json(response);
        })
        .catch((error) => {
            if (!error.response) {
                next(createHttpError(500, "An unknown error occurred"));
            } else if (error.response.status === 400) {
                next(createHttpError(400, error.response.data.error));
            } else if (error.response.status === 415) {
                next(
                    createHttpError(
                        415,
                        "The file uploaded may be invalid. Please try again with a different file."
                    )
                );
            } else {
                next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

router.get("/all", requiresAuth, (req, res, next) => {
    quizGetAll(req.user.id)
        .then((response) => {
            res.status(200).json(response);
        })
        .catch((error) => {
            console.log(error);
            next(createHttpError(500, "An unknown error occurred"));
        });
});

router.get("/:id", requiresAuth, (req, res, next) => {
    // Check if quiz id is provided
    if (!req.params.id) {
        next(createHttpError(400, "Quiz ID not provided"));
        return;
    }

    quizGet(req.params.id, req.user.id)
        .then((response) => {
            res.status(200).json(response);
        })
        .catch((error) => {
            console.log(error);

            if (!error.response) {
                next(createHttpError(500, "An unknown error occurred"));
            } else if (error.response.status === 400) {
                next(createHttpError(400, "Missing parameters"));
            } else if (error.response.status === 403) {
                next(
                    createHttpError(403, "You do not have access to this quiz")
                );
            } else if (error.response.status === 404) {
                next(createHttpError(404, "Quiz not found"));
            } else {
                next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

router.delete("/:id", requiresAuth, (req, res, next) => {
    quizDelete(req.params.id, req.user.id)
        .then((response) => {
            res.status(204).send();
        })
        .catch((error) => {
            console.log(error);

            if (!error.response) {
                next(createHttpError(500, "An unknown error occurred"));
            } else if (error.response.status === 400) {
                next(createHttpError(400, "Missing parameters"));
            } else if (error.response.status === 403) {
                next(
                    createHttpError(403, "You do not have access to this quiz")
                );
            } else if (error.response.status === 404) {
                next(createHttpError(404, "Quiz not found"));
            } else {
                next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

router.post("/:id/leave", requiresAuth, (req, res, next) => {
    quizLeave(req.params.id, req.user.id)
        .then((response) => {
            res.status(204).send();
        })
        .catch((error) => {
            console.log(error);

            if (!error.response) {
                next(createHttpError(500, "An unknown error occurred"));
            } else if (error.response.status === 400) {
                next(createHttpError(400, "Cannot remove user from quiz"));
            } else if (error.response.status === 404) {
                next(createHttpError(404, "Quiz not found"));
            } else {
                next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

router.post("/:id/answer", requiresAuth, (req, res, next) => {
    quizAnswer(req.params.id, req.user.id, req.body)
        .then((response) => {
            res.status(200).json(response);
        })
        .catch((error) => {
            console.log(error);

            if (!error.response) {
                next(createHttpError(500, "An unknown error occurred"));
            } else if (error.response.status === 400) {
                next(createHttpError(400, error.response.data.error));
            } else if (error.response.status === 403) {
                next(
                    createHttpError(403, "You do not have access to this quiz")
                );
            } else if (error.response.status === 404) {
                next(createHttpError(404, "Quiz not found"));
            } else {
                next(createHttpError(500, "An unknown error occurred"));
            }
        });
});

export default router;
