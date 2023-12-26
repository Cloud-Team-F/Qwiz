var app = new Vue({
    el: "#app",
    data: {
        user: null,
        inputs: {
            username: "",
            password: "",
        },
        errorMessage: null,
        successMessage: null,
        loadingScreen: false,
        loading: false,
        mode: 'login'
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
            const file = event.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append("file", file);
    
                // Send the file to the server using an API endpoint
                this.sendFile(formData);
            }
        },
    },
});

function connect() {
    axios
        .get("/api/auth/me")
        .then((res) => {
            console.log(res.data);
            app.user = res.data;
        })
        .catch((err) => {
            console.log("User not logged in");
        })
        .finally(() => {
            app.loadingScreen = false;
        });
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
