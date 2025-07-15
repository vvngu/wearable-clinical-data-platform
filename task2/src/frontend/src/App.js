import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

const App = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    user_id: 'synthetic_user_001',
    metric_type: 'heart_rate',
    start_date: '2024-01-01',
    end_date: '2024-01-02',
    limit: 100
  });

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get('/api/v1/metrics', {
        params: formData
      });
      
      // Format data for chart
      const chartData = response.data.data.map(item => ({
        timestamp: new Date(item.timestamp).toLocaleTimeString(),
        value: item.value,
        fullTimestamp: item.timestamp
      }));
      
      setData(chartData);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Fitbit Data Dashboard</h1>
        <p>Clinical Trial Time-Series Visualization</p>
      </header>

      <main className="App-main">
        <div className="controls">
          <h2>Query Parameters</h2>
          <form onSubmit={handleSubmit} className="form">
            <div className="form-group">
              <label>User ID:</label>
              <input
                type="text"
                name="user_id"
                value={formData.user_id}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Metric Type:</label>
              <select
                name="metric_type"
                value={formData.metric_type}
                onChange={handleInputChange}
                required
              >
                <option value="heart_rate">Heart Rate</option>
                <option value="breathing_rate_deep_sleep_br">Breathing Rate (Deep Sleep)</option>
                <option value="breathing_rate_rem_sleep_br">Breathing Rate (REM Sleep)</option>
                <option value="active_zone_total_minutes">Active Zone Minutes</option>
                <option value="spo2">SpO2</option>
              </select>
            </div>

            <div className="form-group">
              <label>Start Date:</label>
              <input
                type="date"
                name="start_date"
                value={formData.start_date}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>End Date:</label>
              <input
                type="date"
                name="end_date"
                value={formData.end_date}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Limit:</label>
              <input
                type="number"
                name="limit"
                value={formData.limit}
                onChange={handleInputChange}
                min="1"
                max="10000"
                required
              />
            </div>

            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? 'Loading...' : 'Fetch Data'}
            </button>
          </form>
        </div>

        <div className="chart-container">
          <h2>Time-Series Visualization</h2>
          
          {error && (
            <div className="error">
              <p>Error: {error}</p>
            </div>
          )}

          {loading && (
            <div className="loading">
              <p>Loading data...</p>
            </div>
          )}

          {data.length > 0 && !loading && (
            <div className="chart">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tick={{ fontSize: 12 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(label) => `Time: ${label}`}
                    formatter={(value) => [`${value}`, formData.metric_type]}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#2563eb" 
                    strokeWidth={2}
                    dot={{ r: 1 }}
                    name={formData.metric_type}
                  />
                </LineChart>
              </ResponsiveContainer>
              
              <div className="data-info">
                <p><strong>Total Records:</strong> {data.length}</p>
                <p><strong>User:</strong> {formData.user_id}</p>
                <p><strong>Metric:</strong> {formData.metric_type}</p>
                <p><strong>Date Range:</strong> {formData.start_date} to {formData.end_date}</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
