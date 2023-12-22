var socket = null;

//Prepare game
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
    },
    mounted: function () {
        connect();
    },
    methods: {
        advance() {},
        clearLoginInputs() {
            this.inputs.username = "";
            this.inputs.password = "";
        },
        login() {
            axios
                .post("/auth/login", {
                    username: this.inputs.username,
                    password: this.inputs.password,
                })
                .then((res) => {
                    console.log(res);
                    this.user = res.data;
                    this.clearLoginInputs();
                })
                .catch((err) => {
                    this.fail(err.response.data.error);
                });
        },
        register() {
            axios
                .post("/auth/register", {
                    username: this.inputs.username,
                    password: this.inputs.password,
                })
                .then((res) => {
                    console.log(res);
                    this.user = res.data;
                    this.clearLoginInputs();
                    this.success("Successfully registered!");
                })
                .catch((err) => {
                    this.fail(err.response.data.error);
                });
        },
        logout() {
            axios
                .post("/auth/logout")
                .then((res) => {
                    console.log(res);
                    this.user = null;
                })
                .catch((err) => {
                    this.fail(err.response.data.error);
                });
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
    },
});

function connect() {
    const user = axios.get("/auth/me").then((res) => {
        console.log(res.data);
        app.user = res.data;
    });
}
