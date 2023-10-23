import React, { useState, useEffect } from 'react';
import { socket } from '../SocketInstance.js';
import { Link } from 'react-router-dom';

const Login = (props) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginStatus, setLoginStatus] = useState(null);

  useEffect(() => {
    socket.on('login_status', (data) => {
      if (data.success) {
        props.setIsAuthenticated(true);
      } else {
        setLoginStatus('Failed to log in.');
      }
    });

    return () => {
      socket.off('login_status');
    };
  }, [props]);

  const handleSubmit = (e) => {
    e.preventDefault();
    socket.emit('login', { username, password });
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <label>
          Username:
          <input type="text" value={username} onChange={e => setUsername(e.target.value)} />
        </label>
        <label>
          Password:
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
        </label>
        <button type="submit">Login</button>
        {loginStatus && <div>{loginStatus}</div>}
      </form>
      <Link to={"/signup"}>Don't have an account? Sign up here.</Link>
    </div>
  );
};

export default Login;