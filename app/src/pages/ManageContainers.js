import React, { useState, useEffect } from 'react';
import { socket } from '../SocketInstance.js';

const ManageContainers = () => {
  const [imageVersionData, setImageVersionData] = useState({});
  const [selectedImage, setSelectedImage] = useState("");
  const [selectedVersion, setSelectedVersion] = useState("");
  const [versions, setVersions] = useState([]);
  const [activeContainers, setActiveContainers] = useState([]);

  useEffect(() => {
    socket.on('image_version_data', data => {
      setImageVersionData(data);
    });
    socket.emit('image_version_data');

    socket.on('active_containers', data => {
      setActiveContainers(data);
    });
    socket.emit('get_active_containers');

    return () => {
      socket.off('image_version_data');
      socket.off('active_containers');
    };
  }, []);

  const startContainer = () => {
    socket.emit('start_container', { image: selectedImage, version: selectedVersion });
  };

  const stopContainer = (containerId) => {
    socket.emit('stop_container', { id: containerId });
  };

  const updateVersions = (e) => {
    const image = e.target.value;
    setSelectedImage(image);
    setVersions(imageVersionData[image] || []);
  };

  const updateSelectedVersion = (e) => {
    setSelectedVersion(e.target.value);
  };

  return (
    <div>
      <h1>Manage Containers</h1>
      <label>
        Choose an image:
        <select value={selectedImage} onChange={updateVersions}>
          {Object.keys(imageVersionData).map(image => (
            <option key={image} value={image}>{image}</option>
          ))}
        </select>
      </label>
      <label>
        Choose a Version:
        <select value={selectedVersion} onChange={updateSelectedVersion}>
          {versions.map(version => (
            <option key={version} value={version}>{version}</option>
          ))}
        </select>
      </label>
      <button onClick={startContainer}>Start Container</button>
      <h2>Active Containers</h2>
      <ul>
        {activeContainers.map(container => (
          <li key={container.id}>
            {container.image}:{container.version}
            <button onClick={() => stopContainer(container.id)}>Stop</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ManageContainers;