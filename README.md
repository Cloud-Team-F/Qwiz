<p align="center">
  <a href="" rel="noopener">
  <img src="/etc/public/banner.png" alt="Project logo"></a>
</p>
<h3 align="center">Qwiz</h3>

---

<p align="center"> Qwiz transforms how students revise class material by creating AI-powered quizzes.
</p>

## 📝 Table of Contents

- [📝 Table of Contents](#-table-of-contents)
- [💡 Idea ](#-idea-)
- [📃 Design](#-design)
- [🏁 Getting Started ](#-getting-started-)
  - [Prerequisites](#prerequisites)
  - [Manual Setup](#manual-setup)
  - [Docker Setup](#docker-setup)
    - [Note](#note)
- [🎈 Usage ](#-usage-)
- [🚀 Future Scope ](#-future-scope-)
- [⛏️ Built With ](#️-built-with-)

## 💡 Idea <a name = "idea"></a>

- Condensing large amounts of different sources.
- Testing themselves effectively in an interactive way that covers all material.
- Make revising fun and social.
- Variety of questions
  - Multiple choice
  - Fill in the blank
  - Short answer

## 📃 Design
<img src="/etc/public/sysarch.png" alt="System Archiecture Design"></a>


## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development
and testing purposes.

### Prerequisites

You will need to set these services up:
- [Azure Functions](https://azure.microsoft.com/en-us/services/functions/)
- [Azure Cosmos DB for NoSQL](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/)
- [Azure Web PubSub](https://azure.microsoft.com/en-us/services/web-pubsub/)
- [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/)
- [Azure Storage Queue](https://azure.microsoft.com/en-us/services/storage/queues/)
- [Azure Speech Service](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/)
- [OpenAI API](https://openai.com/api)

### Manual Setup

This will walk you through how to set up the project manually on your local machine. Please ensure you have all the appropriate cloud services set up.

To set up the project manually on your local machine, you need to create two configuration files:

1. `local.settings.json` in the `azure` directory: This file should contain the necessary configuration for the Azure function.
You can find an example of this file in the `azure` directory named `example.local.settings.json`. Copy the contents of the example file into your `local.settings.json` file and replace the placeholder values with your actual values.

2. `.env` in the `server` directory: This file should contain the necessary environment variables for the server.
Similarly, you can find an example of this file in the `server` directory named `.example.env`.


To run the Azure Functions locally:
```bash
cd azure
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
func start
```
- This should start the Azure Functions locally on port 7071.

To run the Express server locally:
```bash
cd server
npm install
npm start
```
- This should start the Express server locally on port 5000.

You can now access the site at http://localhost:5000/.

### Docker Setup

These steps will guide you through running the website locally using Docker.

1. Ensure you have Docker and Docker Compose installed on your machine. If not, you can download them from [Docker's official website](https://www.docker.com/products/docker-desktop).
2. Clone the repository to your local machine.
3. In the root directory of the project, you'll find two example environment files: `.example.azure.env` and `.example.server.env`.
4. Create two new files named `.azure.env` and `.server.env` respectively in the root directory, and copy the contents of the example files into them. Replace the placeholder values with your actual values.

You can now build the Docker images and start the containers using Docker Compose:
```bash
docker-compose up
```
You can access the site at http://localhost:5000.

#### Note
Locally, the Azure Functions in the docker container will use the master key at `etc\test-secrets\host.json` for authentication.
By default this is set to `"test"`.
Please ensure that the variable `AZURE_FUNCTION_TOKEN` in `.server.env` matches that key.

## 🎈 Usage <a name="usage"></a>

Features:
- Login, register, logout
- Create new quiz
- View quiz
- Invite friends
- Start quiz
- Answer quiz
- View result
- Delete/leave quiz

Demo:
<img src="/etc/public/demo.gif" alt="Project Demo GIF"></a>

## 🚀 Future Scope <a name = "future_scope"></a>

Due to the scope of the project, there were features that we set aside for future implementation.
These include:
- Invitation system
- Enhanced leaderboard
- More question types

## ⛏️ Built With <a name = "tech_stack"></a>

- [Azure Functions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview) - Serverless Functions
- [Azure CosmosDB](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/) - No-SQL Database
- [ExpressJS](https://expressjs.com/) - Backend Framework
- [VueJs](https://vuejs.org/) - Web Framework
