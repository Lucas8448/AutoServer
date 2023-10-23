import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { socket } from './SocketInstance.js';
import Login from './pages/Login';
import SignUp from './pages/SignUp.js';
import ManageContainers from './pages/ManageContainers.js';

const AuthenticatedRoutes = () => {
  const [authenticated, setAuthenticated] = useState(false);
  const navigate = useNavigate();

  const setIsAuthenticated = (authStatus) => {
    setAuthenticated(authStatus);
  };
  
  

  useEffect(() => {
    socket.on('auth_status', (data) => {
      console.log("Received data from socket:", data);
      if (data.authenticated) {
        setAuthenticated(true);
        console.log("Navigating to /manage_containers");
        navigate('/manage_containers');
      } else {
        setAuthenticated(false);
        console.log("Navigating to /login");
        navigate('/login');
      }
    });

    return () => {
      socket.off('auth_status');
    };
  }, [navigate]);

  useEffect(() => {
    console.log("Authenticated state changed:", authenticated);
  }, [authenticated]);

  return (
    <Routes>
      <Route path="/" element={authenticated ? <ManageContainers /> : <Login setIsAuthenticated={setIsAuthenticated}/>} />
      <Route path="/manage_containers" element={authenticated ? <ManageContainers /> : <Login setIsAuthenticated={setIsAuthenticated}/>} />
      <Route path="/login" element={<Login setIsAuthenticated={setIsAuthenticated}/>} />
      <Route path="/signup" element={<SignUp setIsAuthenticated={setIsAuthenticated}/>} />
    </Routes>
  );
};

const App = () => {
  return (
    <Router>
      <AuthenticatedRoutes />
    </Router>
  );
};

export default App;