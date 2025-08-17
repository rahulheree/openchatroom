OpenChatRoom 🌌

A modern, real-time chat application with a stunning "Aurora Glass" frontend and a scalable FastAPI backend. Built for seamless guest access, instant messaging, and a delightful user experience.

✨ Features

Guest-Friendly Login: No passwords or emails needed—just enter your name to start chatting.

Real-Time Messaging: Powered by WebSockets and Redis Pub/Sub for instant message delivery.

Public & Private Rooms: Create public rooms for anyone or private rooms with invite-only links.

Invitation Links: Generate personal links to restore your session on new devices (expires in 24 hours).

Aesthetic Frontend: Glassmorphic UI with neon glows, smooth animations, and a cosmic aurora background, built with React, Tailwind CSS, and Framer Motion.

Scalable Backend: FastAPI with SQLAlchemy, PostgreSQL, and Redis ensures performance and reliability.

Interactive Features:

Pulsing unread message indicators.

Bouncing typing indicators.

Collapsible member panels.

Room deletion for owners.



🛠️ Tech Stack
Frontend:

React
Tailwind CSS
Framer Motion
Axios

Backend:

FastAPI

SQLAlchemy (with asyncpg)

PostgreSQL

Redis

Python (itsdangerous for secure tokens)

📦 Setup Instructions
Prerequisites

Node.js (for frontend): Download from nodejs.org.

Python 3.8+ (for backend): Download from python.org.

PostgreSQL: Install and set up a local database.

Redis: Install and run a Redis server.

Backend Setup

Clone the repository:

bashgit clone [your-repo-link]

cd openchatroom

Create a virtual environment and install dependencies:

bashpython -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt


Copy .env.example to .env and fill in your details:

plaintextDATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/yourdb

REDIS_URL=redis://localhost:6379

SESSION_SECRET_KEY=your-super-secret-random-key-here

Start the backend server:

bashuvicorn main:app --reload


Frontend Setup

Navigate to the frontend directory:

bashcd chat-frontend

Install dependencies:

bashnpm install

Start the frontend server:

bashnpm run dev

Database Initialization

The backend automatically creates the necessary tables on startup. Ensure your PostgreSQL database is running and accessible.

🚀 Usage

Open the frontend in your browser (e.g., http://localhost:5173).
Enter a name to log in.
Create or join rooms from the "My Feed" or "Public Feed" tabs.

Chat in real-time, generate invitation links, or delete rooms you own.

Open the invitation link in a new device to restore your session.

🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request with your ideas or improvements.

📜 License

This project is licensed under the MIT License.
