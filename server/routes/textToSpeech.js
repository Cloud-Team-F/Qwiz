import NodeCache from "node-cache";
import createHttpError from "http-errors";
import express from "express";
import { requiresAuth } from "../middleware/requiresAuth.js";
import { textToSpeech } from "..//utils/azure.js";

const router = express.Router();

const myCache = new NodeCache({ stdTTL: 172800, checkperiod: 120 });

router.post("/convertToSpeech", requiresAuth, async (req, res, next) => {
    try {
        // Get the text from the request body
        const { text } = req.body;
        console.log(text);

        if (!text) {
            return next(
                createHttpError(400, "Text is required for speech synthesis")
            );
        }

        // Check if the audio data is in the cache
        const cachedData = myCache.get(text);
        if (cachedData) {
            console.log("Returning cached audio data");
            res.setHeader("Content-Type", "audio/wav");
            return res.send(Buffer.from(cachedData));
        }

        // Send the text to the Azure Function
        const data = await textToSpeech(text);

        // Cache the audio data
        myCache.set(text, data);

        // Send the audio data back to the client
        res.setHeader("Content-Type", "audio/wav");
        res.send(Buffer.from(data));
    } catch (error) {
        console.error("Error in speech synthesis:", error);
        next(
            createHttpError(500, "An error occurred while synthesizing speech")
        );
    }
});

export default router;
