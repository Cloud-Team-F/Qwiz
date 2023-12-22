import "dotenv/config.js";

import authRoutes from "./routes/auth.js"
import cookieParser from "cookie-parser";
import createHttpError from "http-errors";
import env from "./utils/validateEnv.js";
import express from "express";
import morgan from "morgan";

const port = env.PORT;

const app = express();

app.use(morgan("dev"));
app.use(express.json());
app.use(cookieParser("elkwgkgnelkrh")); //todo

// Routes
app.use("/auth", authRoutes);

app.use((req, res, next) => {
    next(createHttpError(404, "Endpoint not found"));
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
