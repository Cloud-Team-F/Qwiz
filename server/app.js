import "dotenv/config.js";

import path, { dirname } from "path";

import authRoutes from "./routes/auth.js";
import textToSpeechRoutes from "./routes/textToSpeech.js";
import cookieParser from "cookie-parser";
import createHttpError from "http-errors";
import env from "./utils/validateEnv.js";
import express from "express";
import { fileURLToPath } from "url";
import inviteRoutes from "./routes/invite.js";
import morgan from "morgan";
import quizRoutes from "./routes/quiz.js";

const port = env.PORT;

const app = express();

app.use(morgan("dev"));
app.use(express.json());
app.use(cookieParser("elkwgkgnelkrh")); //todo

// Template engine
app.set("view engine", "ejs");

// Set custom views directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
app.set("views", path.join(__dirname, "../client/views"));
app.use("/static", express.static(path.join(__dirname, "../client/public")));

// Client endpoint
app.get("/", (req, res) => {
    try {
        console.log(path.join(__dirname, "../client/views"));
        res.render("client");
    } catch (e) {
        console.log(e);
    }
});

// Routes
app.use("/api/auth", authRoutes);
app.use("/api/quiz", quizRoutes);
app.use("/api/invite", inviteRoutes);
app.use("/api/tts", textToSpeechRoutes)

app.use((req, res, next) => {
    res.render("404");
});

app.use((error, req, res, next) => {
    let errorMessage = "An unknown error occurred";
    let statusCode = 500;
    if (error instanceof createHttpError.HttpError) {
        statusCode = error.status;
        errorMessage = error.message;
    } else {
        console.log(error);
    }
    res.status(statusCode).json({ error: errorMessage });
});

process.on("uncaughtException", function(error) {
    console.error("Uncaught exception: ", error);
});

app.listen(port, () => {
    console.log("Server running on port: " + port);
});
