import { WebPubSubEventHandler } from "@azure/web-pubsub-express";
import { WebPubSubServiceClient } from "@azure/web-pubsub";
import createHttpError from "http-errors";
import env from "../utils/validateEnv.js";
import express from "express";
import { requiresAuth } from "../middleware/requiresAuth.js";

const router = express.Router();

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

export default router;
