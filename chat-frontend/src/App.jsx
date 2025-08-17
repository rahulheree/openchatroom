import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

// --- API Client Setup ---
// --- THIS IS THE FIX ---
// Changed 127.0.0.1 to localhost to ensure the browser sends the cookie correctly.
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  withCredentials: true,
});

// --- Reusable Components ---
const AuroraBackground = () => (
  <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full filter blur-3xl opacity-20 animate-blob"></div>
    <div className="absolute top-1/2 right-1/4 w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
    <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-teal-500 rounded-full filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
  </div>
);

const LoginScreen = ({ onLogin }) => {
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  const handleStartSession = async () => {
    if (name.trim() === '') {
      setError('Please enter a name.');
      return;
    }
    setError('');
    try {
      const response = await apiClient.post('/session/start', { name });
      onLogin(response.data);
    } catch (err) {
      console.error("Failed to start session:", err);
      setError('Could not connect to the server. Is it running?');
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') handleStartSession();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-md p-8 space-y-6 bg-black/30 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl"
    >
      <h1 className="text-3xl font-bold text-center text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
        Welcome to OpenChatRoom
      </h1>
      <div>
        <label htmlFor="name" className="block mb-2 text-sm font-medium text-gray-400">
          What should we call you?
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Enter your name..."
          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-300"
        />
        {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
      </div>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleStartSession}
        className="w-full py-3 font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg hover:opacity-90 transition-opacity duration-300"
      >
        Start Chatting
      </motion.button>
    </motion.div>
  );
};

// --- Create Room Modal Component ---
const CreateRoomModal = ({ isOpen, onClose, onRoomCreated }) => {
    const [roomName, setRoomName] = useState('');
    const [isPublic, setIsPublic] = useState(true);
    const [error, setError] = useState('');

    const handleCreateRoom = async () => {
        if (roomName.trim() === '') {
            setError('Room name cannot be empty.');
            return;
        }
        try {
            await apiClient.post('/rooms', { name: roomName, is_public: isPublic });
            onRoomCreated(); // Notify parent to refetch rooms
            onClose(); // Close the modal
        } catch (err) {
            console.error("Failed to create room:", err);
            setError('Could not create room.');
        }
    };

    if (!isOpen) return null;

    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex justify-center items-center z-50"
            onClick={onClose}
        >
            <motion.div 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="w-full max-w-md p-6 bg-gray-800/80 rounded-2xl border border-white/10 shadow-lg"
                onClick={e => e.stopPropagation()}
            >
                <h2 className="text-2xl font-bold mb-4">Create a New Room</h2>
                <input
                    type="text"
                    value={roomName}
                    onChange={(e) => setRoomName(e.target.value)}
                    placeholder="Enter room name..."
                    className="w-full px-4 py-2 mb-4 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex items-center mb-4">
                    <input type="checkbox" id="isPublic" checked={isPublic} onChange={() => setIsPublic(!isPublic)} className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"/>
                    <label htmlFor="isPublic" className="ml-2 text-sm font-medium text-gray-300">Public Room</label>
                </div>
                {error && <p className="mb-2 text-sm text-red-400">{error}</p>}
                <div className="flex justify-end gap-4">
                    <button onClick={onClose} className="px-4 py-2 font-semibold text-gray-300 bg-gray-600/50 rounded-lg hover:bg-gray-500/50">Cancel</button>
                    <button onClick={handleCreateRoom} className="px-4 py-2 font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-500">Create</button>
                </div>
            </motion.div>
        </motion.div>
    );
};


// --- Main Chat Interface Component ---
const ChatInterface = ({ user, onLogout }) => {
  const [myRooms, setMyRooms] = useState([]);
  const [publicRooms, setPublicRooms] = useState([]);
  const [activeFeed, setActiveFeed] = useState('my');
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [members, setMembers] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const ws = useRef(null);
  const messagesEndRef = useRef(null);

  const fetchRooms = async () => {
    try {
      const [myRoomsRes, publicRoomsRes] = await Promise.all([
        apiClient.get('/feed/my'),
        apiClient.get('/feed/public'),
      ]);
      setMyRooms(myRoomsRes.data);
      setPublicRooms(publicRoomsRes.data);
    } catch (error) {
      console.error("Failed to fetch rooms:", error);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!selectedRoom) return;

    const fetchRoomDetails = async () => {
      try {
        const [messagesRes, membersRes] = await Promise.all([
          apiClient.get(`/rooms/${selectedRoom.id}/messages`),
          apiClient.get(`/rooms/${selectedRoom.id}/members`),
        ]);
        setMessages(messagesRes.data.reverse());
        setMembers(membersRes.data);
      } catch (error) {
        console.error("Failed to fetch room details:", error);
      }
    };
    fetchRoomDetails();

    const wsUrl = `ws://localhost:8000/api/v1/ws/${selectedRoom.id}`;
    ws.current = new WebSocket(wsUrl);
    ws.current.onopen = () => console.log("WebSocket connected");
    ws.current.onclose = () => console.log("WebSocket disconnected");
    ws.current.onmessage = (event) => {
      const messageData = JSON.parse(event.data);
      setMessages((prevMessages) => [...prevMessages, messageData]);
    };
    
    return () => {
      if (ws.current) ws.current.close();
    };
  }, [selectedRoom]);

  const handleSendMessage = () => {
    if (newMessage.trim() && ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(newMessage);
      setNewMessage('');
    }
  };
  
  const handleRoomSelect = async (room) => {
    const isMember = myRooms.some(myRoom => myRoom.id === room.id);
    if (!isMember && room.is_public) {
        try {
            await apiClient.post(`/rooms/${room.id}/join`);
            await fetchRooms();
        } catch (error) {
            console.error("Failed to join room:", error);
            return;
        }
    }
    setSelectedRoom(room);
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') handleSendMessage();
  };

  const roomsToDisplay = activeFeed === 'my' ? myRooms : publicRooms;

  return (
    <>
      <CreateRoomModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setCreateModalOpen(false)} 
        onRoomCreated={fetchRooms}
      />
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="w-full flex-1 p-4 flex gap-4 overflow-hidden"
      >
        {/* Column 1: Left Sidebar */}
        <div className="w-1/4 h-full bg-black/30 backdrop-blur-xl rounded-2xl border border-white/10 p-4 flex flex-col">
          <div className="flex justify-between items-center mb-4 pb-4 border-b border-white/10">
            <div>
              <p className="text-sm text-gray-400">Logged in as</p>
              <h3 className="text-lg font-bold text-white">{user.name}</h3>
            </div>
            <button onClick={onLogout} className="px-3 py-1 text-xs font-semibold text-gray-300 bg-red-600/50 rounded-lg hover:bg-red-500/50">
              Logout
            </button>
          </div>
          
          <div className="flex border-b border-white/10 mb-4">
            <button onClick={() => setActiveFeed('my')} className={`flex-1 p-2 font-semibold transition-colors ${activeFeed === 'my' ? 'text-blue-400' : 'text-gray-400 hover:text-white'}`}>My Feed</button>
            <button onClick={() => setActiveFeed('public')} className={`flex-1 p-2 font-semibold transition-colors ${activeFeed === 'public' ? 'text-blue-400' : 'text-gray-400 hover:text-white'}`}>Public</button>
          </div>
          <ul className="space-y-2 overflow-y-auto flex-1">
            {roomsToDisplay.map(room => (
              <li key={room.id} onClick={() => handleRoomSelect(room)} className={`p-3 rounded-lg cursor-pointer transition-all ${selectedRoom?.id === room.id ? 'bg-blue-500/30' : 'bg-white/5 hover:bg-white/10'}`}>
                <p className="font-semibold flex items-center gap-2">
                  {room.name}
                  {room.owner.id === user.id && <span title="You are the owner">👑</span>}
                </p>
                <div className="flex justify-between items-center text-xs text-gray-400">
                  <span>Owner: {room.owner.name}</span>
                  <span className="flex items-center gap-1 text-green-400">
                    <div className="w-2 h-2 rounded-full bg-green-400"></div>
                    {room.active_users}
                  </span>
                </div>
              </li>
            ))}
          </ul>
          <motion.button onClick={() => setCreateModalOpen(true)} whileHover={{ scale: 1.05 }} className="mt-4 w-full py-2 font-semibold text-white bg-gradient-to-r from-teal-500 to-cyan-600 rounded-lg">+</motion.button>
        </div>

        {/* Column 2: Center Chat Window */}
        <div className="w-1/2 h-full bg-black/20 backdrop-blur-lg rounded-2xl border border-white/10 p-4 flex flex-col">
          {selectedRoom ? (
            <>
              <div className="border-b border-white/10 pb-2 mb-4">
                <h2 className="text-xl font-bold">{selectedRoom.name}</h2>
              </div>
              <div className="flex-1 overflow-y-auto pr-2">
                {messages.map((msg, index) => (
                  <motion.div 
                    key={index} 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex mb-4 ${msg.author.id === user.id ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`p-3 rounded-lg max-w-xs ${msg.author.id === user.id ? 'bg-blue-600/50' : 'bg-gray-700/50'}`}>
                      <p className="font-bold text-xs text-purple-300">{msg.author.name}</p>
                      <p>{msg.content}</p>
                    </div>
                  </motion.div>
                ))}
                <div ref={messagesEndRef} />
              </div>
              <div className="mt-4 flex gap-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <motion.button onClick={handleSendMessage} whileTap={{ scale: 0.95 }} className="px-4 py-2 font-semibold bg-blue-600 rounded-lg">Send</motion.button>
              </div>
            </>
          ) : (
            <div className="flex flex-col justify-center items-center h-full">
              <h2 className="text-2xl font-bold text-gray-300">Select a room to start chatting</h2>
              <p className="text-gray-500">Or create a new one using the '+' button.</p>
            </div>
          )}
        </div>

        {/* Column 3: Right Room Info */}
        <div className="w-1/4 h-full bg-black/30 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
          {selectedRoom ? (
            <>
              <h2 className="text-xl font-bold mb-4">Members ({members.length})</h2>
              <ul className="space-y-2">
                {members.map(member => (
                  <li key={member.id} className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400"></div>
                    <span>{member.name}</span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <div className="flex flex-col justify-center items-center h-full">
              <h2 className="text-xl font-bold text-gray-400">Room Info</h2>
              <p className="text-gray-500">Select a room to see details.</p>
            </div>
          )}
        </div>
      </motion.div>
    </>
  );
};


// --- Main App Component ---
function App() {
  const [user, setUser] = useState(null);

  const handleLogout = () => {
    setUser(null);
  };

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await apiClient.get('/session/me');
        setUser(response.data);
      } catch (error) {
        console.log("No active session found.");
      }
    };
    checkSession();
  }, []);

  return (
    <main className="relative flex items-center justify-center min-h-screen bg-[#101418] font-sans text-white overflow-hidden">
      <AuroraBackground />
      <AnimatePresence mode="wait">
        {!user ? (
          <LoginScreen key="login" onLogin={setUser} />
        ) : (
          <motion.div 
            key="app-wrapper"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full h-screen flex flex-col"
          >
            <header className="p-4 border-b border-white/10 backdrop-blur-xl bg-black/30 flex-shrink-0">
              <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
                OpenChatRoom
              </h1>
            </header>
            <ChatInterface user={user} onLogout={handleLogout} />
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}

export default App;



