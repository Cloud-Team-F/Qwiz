import createHttpError from "http-errors";
import express from "express";
import { requiresAuth } from "../middleware/requiresAuth.js";
import { textToSpeech } from "..//utils/azure.js";

const router = express.Router();

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

        // Send the text to the Azure Function
        const data = await textToSpeech(text);

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
