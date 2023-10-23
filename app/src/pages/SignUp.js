import React, { useState, useEffect } from 'react';
import { socket } from '../SocketInstance.js';
import { Link } from 'react-router-dom';

const SignUp = (props) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [signupStatus, setSignupStatus] = useState(null);

  useEffect(() => {
    socket.on('signup_status', (data) => {
      if (data.success) {
        props.setIsAuthenticated(true);
      } else {
        setSignupStatus('Failed to sign up.');
      }
    });

    return () => {
      socket.off('signup_status');
    };
  }, [props]);

  const handleSubmit = (e) => {
    e.preventDefault();
    socket.emit('signup', { username, password });
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
        <button type="submit">Sign Up</button>
        {signupStatus && <div>{signupStatus}</div>}
      </form>
      <Link to="/login">Already have an account? Log in here.</Link>
    </div>
  );
};

export default SignUp;