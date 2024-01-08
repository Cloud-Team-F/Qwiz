import { port, str } from "envalid/dist/validators.js";

import { cleanEnv } from "envalid";

export default cleanEnv(process.env, {
    PORT: port(),
    AZURE_FUNCTION_URL: str(),
    AZURE_FUNCTION_TOKEN: str(),
    JWT_SECRET: str(),
    PUBSUB_CONNECTION_STRING: str(),
    COOKIE_SECRET: str(),
});
