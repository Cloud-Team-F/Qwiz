import { quizCreate, quizGetAll } from "../utils/azure.js";

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
const supportedFileTypes = ["application/pdf"];

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
    // Check if quiz name is provided
    if (!req.body["quiz_name"]) {
        next(createHttpError(400, "Quiz name not provided"));
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

    // Check there are files
    if (req.files && req.files.length === 0) {
        next(createHttpError(400, "No files uploaded"));
        return;
    }
    if (req.files.length > 5) {
        next(createHttpError(400, "Maximum 5 files allowed"));
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

export default router;
