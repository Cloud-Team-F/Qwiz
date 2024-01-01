import express from 'express';
import createHttpError from 'http-errors';
import axios from 'axios'; 
import { requiresAuth } from "../middleware/requiresAuth.js"

const router = express.Router();

const azureFunctionUrl = 'http://localhost:7071/convertToSpeech'; 

router.post('/convertToSpeech', requiresAuth,async (req, res, next) => {
    try {
        const { text } = req.body;

        console.log(text);

        if (!text) {
            return next(createHttpError(400, 'Text is required for speech synthesis'));
        }


        // Send the text to the Azure Function
        const response = await axios.post(azureFunctionUrl, { text },{responseType: 'arraybuffer'});


        // Send the audio data back to the client
        res.setHeader('Content-Type', 'audio/wav');
        res.send(Buffer.from(response.data));
    } catch (error) {
        console.error('Error in speech synthesis:', error);
        next(createHttpError(500, 'An error occurred while synthesizing speech'));
    }
});

export default router;
