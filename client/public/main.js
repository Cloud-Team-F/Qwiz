let ws = null;

var app = new Vue({
    el: "#app",
    data: {
        user: null,
        inputs: {
            username: "",
            password: "",
            inviteCode: "",
            quizName: "",
            quizText: "",
        },
        errorMessage: null,
        successMessage: null,
        loadingScreen: false,
        loading: false,
        mode: "login",
        creatingQuiz: false,
        filesUploaded: [],
    },
    mounted: function () {
        this.loadingScreen = true;
        connect();
    },
    methods: {
        advance() {},
        toggleMode(newMode) {
            this.mode = newMode;
        },
        clearLoginInputs() {
            this.inputs.username = "";
            this.inputs.password = "";
        },
        login() {
            sendRequest(
                "POST",
                "/api/auth/login",
                {
                    username: this.inputs.username,
                    password: this.inputs.password,
                },
                (res) => {
                    console.log(res);
                    this.user = res.data;
                    connectPubSub();
                    this.clearLoginInputs();
                },
                (err) => {
                    this.fail(err.response.data.error);
                }
            );
        },
        register() {
            sendRequest(
                "POST",
                "/api/auth/register",
                {
                    username: this.inputs.username,
                    password: this.inputs.password,
                },
                (res) => {
                    console.log(res);
                    this.user = res.data;
                    connectPubSub();
                    this.clearLoginInputs();
                    this.success("Successfully registered!");
                },
                (err) => {
                    this.fail(err.response.data.error);
                }
            );
        },
        logout() {
            axios;
            sendRequest(
                "POST",
                "/api/auth/logout",
                null,
                (res) => {
                    console.log(res);
                    this.user = null;
                    disconnectPubSub();
                },
                (err) => {
                    this.fail(err.response.data.error);
                }
            );
        },
        fail(message) {
            this.errorMessage = message;
            setTimeout(() => {
                this.errorMessage = null;
            }, 3000);
        },
        success(message) {
            this.successMessage = message;
            setTimeout(() => {
                this.successMessage = null;
            }, 3000);
        },
        sendFile(formData) {
            sendRequest(
                "POST",
                "/api/upload",
                formData,
                (res) => {
                    // Handle a successful file upload response from the server
                    console.log(res.data.message);
                },
                (err) => {
                    // Handle errors, such as file size limits, if necessary
                    console.error(err.response.data.error);
                },
                false // Set loadingScreen to false to prevent showing a loading screen
            );
        },
        uploadFile(event) {
            console.log("Uploading file...");
            const file = event.target.files[0];

            if (this.filesUploaded.length < 5) {
                console.log(file);
                this.filesUploaded.push(file.name);
                if (file) {
                    const formData = new FormData();
                    formData.append("file", file);

                    // Send the file to the server using an API endpoint
                    this.sendFile(formData);
                }
            } else {
                this.fail("Maximum 5 files allowed");
            }
        },
        createQuiz() {
            this.creatingQuiz = true;
        },
        closeCreateQuiz() {
            this.creatingQuiz = false;
        },
    },
});

function connect() {
    // Check if user is logged in
    axios
        .get("/api/auth/me")
        .then((res) => {
            console.log(res.data);
            app.user = res.data;

            // Connect to pubsub
            connectPubSub();
        })
        .catch((err) => {
            console.log("User not logged in");
        })
        .finally(() => {
            app.loadingScreen = false;
        });
}

function connectPubSub() {
    // Connect to Web PubSub
    axios
        .get("/api/quiz/negotiate")
        .then((res) => {
            ws = new WebSocket(res.data.url, "json.webpubsub.azure.v1");
            ws.onopen = () => console.log("connected");

            ws.onmessage = (event) => {
                // convert to JSON
                try {
                    event_data = JSON.parse(event.data);
                } catch (e) {
                    console.log(e);
                }
                if (
                    event_data.data &&
                    event_data.data.type &&
                    event_data.data.type === "quiz_processed"
                ) {
                    app.success("Your quiz has been created!");
                }
                console.log(event_data);
            };

            ws.onclose = () => console.log("disconnected");
        })
        .catch((err) => {
            console.log(err);
        });
}

function disconnectPubSub() {
    if (ws) {
        ws.close();
    }
}

function sendRequest(
    method,
    url,
    data,
    callback,
    callbackError,
    loadingScreen = true
) {
    app.loading = true;
    app.loadingScreen = loadingScreen;

    axios(
        {
            method: method,
            url: url,
            data: data,
        },
        {
            headers: {
                "Content-Type": "application/json",
            },
        }
    )
        .then((res) => {
            console.log(res);
            callback(res);
        })
        .catch((err) => {
            if (err.code === "ERR_NETWORK") {
                app.fail("Unable to connect to server");
                return;
            }
            callbackError(err);
        })
        .finally(() => {
            app.loading = false;
            app.loadingScreen = false;
        });
}
