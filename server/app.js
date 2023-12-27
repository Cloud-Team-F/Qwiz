import "dotenv/config.js";

import path, { dirname } from "path";

import authRoutes from "./routes/auth.js";
import cookieParser from "cookie-parser";
import createHttpError from "http-errors";
import env from "./utils/validateEnv.js";
import express from "express";
import { fileURLToPath } from "url";
import morgan from "morgan";
import multer from "multer";
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

app.use((req, res, next) => {
    res.render("404");
});

app.use((error, req, res, next) => {
    let errorMessage = "An unknown error occurred";
    let statusCode = 500;
    if (error instanceof createHttpError.HttpError) {
        statusCode = error.status;
        errorMessage = error.message;
    }
    res.status(statusCode).json({ error: errorMessage });
});

app.listen(port, () => {
    console.log("Server running on port: " + port);
});

// Create a multer instance for file uploads
const upload = multer({ dest: "uploads/" }); // Define the destination folder for uploaded files

// Create an API endpoint for file uploads
app.post("/api/upload", upload.single("file"), (req, res) => {
    // Access the uploaded file through req.file
    const uploadedFile = req.file;
    if (!uploadedFile) {
        console.log("Error - no file uploaded");
        return res.status(400).json({ error: "No file uploaded" });
    }

    // Process the uploaded file (e.g., store it, use it for OpenAI prompt, etc.)
    // Implement the necessary logic here based on your requirements.

    // Send a response to the client
    console.log("File uploaded successfully");
    res.json({ message: "File uploaded successfully" });
});
