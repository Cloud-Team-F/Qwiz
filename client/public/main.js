let ws = null;
const supportedFileTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
];

// STATES = [
//     'LOGIN',
//     'MENU',
//     'CREATE-QUIZ-1',
//     'CREATE-QUIZ-2',
//     'VIEW-QUIZ'
// ]

var app = new Vue({
    el: "#app",
    data: {
        // Loading states
        loadingScreen: false,
        loading: false,
        loadingQuizList: true,


        inputs: {
            username: "",
            password: "",
            inviteCode: "",
            quizName: "",
            quizText: "",
            userToInvite: "",
            quizTopic: "",
            numOfQuestions: 10,
            questionTypes: [],
        },
        alertMessages: [],
        mode: "login",
        filesUploaded: [],

        // Data states
        currentState: "LOGIN",
        user: null,
        ownQuizzes: [],
        sharedQuizzes: [],
        currentQuiz: null,
        selectedType: null,
    },
    mounted: function () {
        this.loadingScreen = true;
        connect();
    },
    methods: {
        speakQuestion(question) {
            let currentAudio = null

            console.log('speakQuestion called with',question);
            // The URL of backend endpoint that handles speech synthesis
            const speechSynthesisUrl = '/api/tts/convertToSpeech'

            if (currentAudio) {
                currentAudio.pause()
                currentAudio.currentTime = 0
                
            }
        

            let fullTextToSpeak = `Question ${question.question_id}: `;

            // Extract the text that needs to be spoken
            if (question.type === "fill-gaps") {
                const questionFillBlanks = question.question.replace(/_{2,}/g, 'fill the blank')
                fullTextToSpeak += questionFillBlanks
            }else if (question.type === "short-answer"){
                fullTextToSpeak += question.question


            }else if (question.type === "multi-choice"){
                
                const questionText = `Question ${question.question_id}: ${question.question}`;
                const optionsText = question.options.map((option, index) => `Option ${index + 1}: ${option}`).join('. ');
                fullTextToSpeak = `${questionText}. ${optionsText}`;



            }

        
            // Send the text to the backend for speech synthesis
            axios.post(speechSynthesisUrl, { text: fullTextToSpeak }, {responseType: 'arraybuffer'})
                .then(response => {
                    // Assuming the response contains the audio data in a binary format

                    console.log('recieved res with data size: ' + response.data.size);
                    const audioBlob = new Blob([response.data], { type: 'audio/wav' });
                    console.log('audio blob created with size', audioBlob.size);
                    const audioUrl = URL.createObjectURL(audioBlob);
                    console.log('Audio URL:',audioUrl);
                    currentAudio = new Audio(audioUrl);

                    currentAudio.play().then(()=>{
                        console.log('Audio started successfully');
                    }).catch(playbackError=>{
                        console.error('Error during playing the playback', playbackError)
                    })

                    currentAudio.onended = () =>{
                        console.log('Audio finished playing');
                        currentAudio = null;
                    }
                })
                .catch(error => {
                    console.error('Error synthesizing  the speech:', error);
                    isAudioPlaying = false

                });
        },
        
        advance() {},
        toggleMode(newMode) {
            this.mode = newMode;
        },
        clearLoginInputs() {
            this.inputs.username = "";
            this.inputs.password = "";
        },
        clearQuizInputs() {
            this.inputs.quizName = "";
            this.inputs.quizText = "";
            this.filesUploaded = [];
            this.inputs.quizTopic = "";
            this.inputs.numOfQuestions = 10;
            this.inputs.questionTypes = [];
        },
        clearQuizList() {
            this.ownQuizzes = [];
            this.sharedQuizzes = [];
        },
        backToHome() {
            this.currentState = "MENU";
            this.currentQuiz = null;
        },
        copyInviteCode(inviteCode) {
            navigator.clipboard.writeText(inviteCode);
            this.success("Invite code copied to clipboard!");
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
                    app.currentState = "MENU";
                    connectPubSub();
                    this.updateQuizList();
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
                    app.currentState = "MENU";
                    connectPubSub();
                    this.updateQuizList();
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
                    app.currentState = "LOGIN";
                    this.clearQuizList();
                    disconnectPubSub();
                },
                (err) => {
                    this.fail(err.response.data.error);
                }
            );
        },
        joinQuiz() {
            if (this.inputs.inviteCode == "") {
                this.fail("Enter an invite code to join a quiz!");
            } else {
                sendRequest(
                    "POST",
                    `/api/invite/join/${this.inputs.inviteCode}`,
                    null,
                    (res) => {
                        console.log(res);
                        this.success("Successfully joined quiz!");
                        this.inputs.inviteCode = "";
                        this.updateQuizList();
                    },
                    (err) => {
                        this.fail(err.response.data.error);
                    }
                );
            }
        },
        fail(message) {
            this.alertMessages.push({ type: "error", message: message });
            setTimeout(() => {
                this.alertMessages.shift();
            }, 3000);
        },
        success(message) {
            this.alertMessages.push({ type: "success", message: message });
            setTimeout(() => {
                this.alertMessages.shift();
            }, 3000);
        },
        uploadFile(event) {
            console.log(
                "Uploading file, number of current files: ",
                this.filesUploaded.length
            );
            const file = event.target.files[0];

            if (file.type && !supportedFileTypes.includes(file.type)) {
                // check file type
                this.fail("File type not supported!");
            } else if (this.filesUploaded.length < 3) {
                console.log(file);
                this.filesUploaded.push(file);
            } else {
                this.fail("Too many files! (3 max)");
            }
        },
        continueQuizCreate() {
            const quizName = this.inputs.quizName.trim();
            const quizText = this.inputs.quizText.trim();
            if (quizName == "") {
                this.fail("A quiz name is required!");
            } else if (quizText == "" && this.filesUploaded.length == 0) {
                this.fail("Prompt text or a file upload is required!");
            } else if (quizName.length > 50) {
                this.fail("Quiz name must be less than 50 characters!");
            } else if (
                quizText &&
                (quizText.length < 400 || quizText.length > 2000)
            ) {
                this.fail(
                    "Content text must be between 400 and 2000 characters!"
                );
            } else {
                this.currentState = "CREATE-QUIZ-2";
            }
        },
        updateQuestionTypes(questionType) {
            const index = this.inputs.questionTypes.indexOf(questionType);
            if (index === -1) {
                this.inputs.questionTypes.push(questionType);
            } else {
                this.inputs.questionTypes.splice(index, 1);
            }

            console.log("Question types: ", this.inputs.questionTypes);
        },
        uploadQuiz() {
            console.log("Uploading quiz...");

            const quizTopic = this.inputs.quizTopic.trim();
            if (quizTopic.length > 100) {
                this.fail("Quiz topic must be less than 100 characters!");
                return;
            }

            if (this.inputs.questionTypes.length === 0) {
                this.fail("At least one question type must be selected!");
                return;
            }

            // Create a new FormData instance
            const formData = new FormData();

            // Append text fields
            formData.append("quiz_name", this.inputs.quizName);
            formData.append("content", this.inputs.quizText);

            // Append files
            for (const file of this.filesUploaded) {
                formData.append("files[]", file);
            }

            formData.append("num_questions", this.inputs.numOfQuestions);
            formData.append("topic", this.inputs.quizTopic);
            formData.append("question_types", this.inputs.questionTypes);

            // Ssend request to server
            sendFormData(
                "POST",
                "/api/quiz/create",
                formData,
                (res) => {
                    console.log(res);
                    this.success("Your quiz is being processed!");
                    this.clearQuizInputs();
                    this.updateQuizList();
                    this.closeCreateQuiz();
                },
                (err) => {
                    console.log(err);
                    this.fail(err.response.data.error);
                }
            );
        },
        createQuiz() {
            this.currentState = "CREATE-QUIZ-1";
        },
        createQuizBack() {
            if (this.currentState == "CREATE-QUIZ-1") {
                this.currentState = "MENU";
                this.clearQuizInputs();
            } else if (this.currentState == "CREATE-QUIZ-2") {
                this.currentState = "CREATE-QUIZ-1";
            }
        },
        closeCreateQuiz() {
            this.currentState = "MENU";
            this.clearQuizInputs();
        },
        viewQuiz(quiz) {
            console.log("Current quiz: ", quiz);
            sendRequest(
                "GET",
                `/api/quiz/${quiz.id}`,
                quiz.id,
                (res) => {
                    console.log(res);
                    this.currentQuiz = { ...quiz, ...res.data };
                    this.currentState = "VIEW-QUIZ";
                    console.log("Viewing quiz: ", this.currentQuiz);
                },
                (err) => {
                    this.fail(err.response.data.error);
                },
                true
            );
        },
        updateQuizList() {
            this.loadingQuizList = true;
            sendRequest(
                "GET",
                "/api/quiz/all",
                null,
                (res) => {
                    console.log(res);
                    this.ownQuizzes = res.data.own_quizzes;
                    this.sharedQuizzes = res.data.shared_quizzes;
                    this.loadingQuizList = false;
                },
                (err) => {
                    this.fail(err.response.data.error);
                    this.loadingQuizList = false;
                },
                false
            );
        },
        optionSelected(option, questionId, event) {
            // Prevent the method from running if the radio itself is clicked
            if (event.target.type !== 'radio') {
                // Toggle the answer
                this.currentQuiz.answers[questionId] = this.currentQuiz.answers[questionId] === option ? "" : option;
            }
            // Ensure Vue updates the radio button state
            this.$nextTick(() => {
                this.$forceUpdate();
            });
            console.log('Answers:', this.currentQuiz.answers);
        },        
        startQuiz(quizID) {
            // todo:: change this
            // this.success("Starting quiz: " + quizID);
            sendRequest(
                "GET",
                `/api/quiz/${quizID}`,
                null,
                (res) => {
                    console.log(res);
                    
                    const errored = res.data.errored;
                    if (errored) {
                        this.fail(
                            "This quiz has errored and cannot be started!"
                        );
                        return;
                    }

                    let answers = {};

                    for (let question of res.data.questions) {
                        answers[question.question_id] = "";
                    }

                    this.currentQuiz = res.data;
                    this.currentQuiz.answers = answers;

                    this.currentState = "START-QUIZ";
                    console.log("Starting quiz: ", this.currentQuiz);
                },
                (err) => {
                    this.fail(err.response.data.error);
                },
                true
            );
        },
        removeQuiz(quiz) {
            this.ownQuizzes.filter((item) => item.id == quiz.id);
            this.sharedQuizzes.filter((item) => item.id == quiz.id);
        },
        leaveQuiz(quiz) {
            sendRequest(
                "POST",
                `/api/quiz/${quiz.quiz_id}/leave`,
                quiz,
                (res) => {
                    console.log(res);
                    this.ownQuizzes = this.ownQuizzes.filter(
                        (q) => q.id !== quiz.id
                    );
                    this.sharedQuizzes = this.sharedQuizzes.filter(
                        (q) => q.id !== quiz.id
                    );
                    this.backToHome();
                    this.success("Successfully left quiz!");
                },
                (err) => {
                    this.fail(err.response.data.error);
                },
                true
            );
        },
        deleteQuiz(quiz) {
            sendRequest(
                "DELETE",
                `/api/quiz/${quiz.quiz_id}`,
                quiz,
                (res) => {
                    console.log(res);
                    this.ownQuizzes = this.ownQuizzes.filter(
                        (q) => q.id !== quiz.id
                    );
                    this.sharedQuizzes = this.sharedQuizzes.filter(
                        (q) => q.id !== quiz.id
                    );
                    this.backToHome();
                    this.success("Successfully deleted quiz!");
                },
                (err) => {
                    this.fail(err.response.data.error);
                },
                true
            );
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
            app.currentState = "MENU";
            // Connect to pubsub
            connectPubSub();

            // Update quiz list
            app.updateQuizList();
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
                if (event_data.data && event_data.data.type) {
                    if (event_data.data.type === "quiz_processed") {
                        app.updateQuizList();
                        app.success("Your quiz has been created!");
                    }

                    if (event_data.data.type === "quiz_errored") {
                        app.updateQuizList();
                        app.fail(
                            "Your quiz could not be created! Please try again with different content."
                        );
                    }
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

function sendFormData(method, url, formData, callback, callbackError) {
    app.loading = true;
    app.loadingScreen = true;

    axios({
        method: method,
        url: url,
        data: formData,
        headers: {
            "Content-Type": "multipart/form-data",
        },
    })
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
