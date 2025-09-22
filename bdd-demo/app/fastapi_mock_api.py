"""FastAPI mock API for testing scenarios."""

import random
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BDD Demo Mock API",
    description="Mock API for BDD testing scenarios",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data for testing
SAMPLE_CLIENTS = [
    {
        "client_id": 1,
        "client_name": "Client A",
        "revenue": 150000.50,
        "region": "North",
        "active": True,
        "last_updated": "2024-01-15T10:30:00Z"
    },
    {
        "client_id": 2,
        "client_name": "Client B", 
        "revenue": 275000.75,
        "region": "South",
        "active": True,
        "last_updated": "2024-01-14T14:20:00Z"
    },
    {
        "client_id": 3,
        "client_name": "Client C",
        "revenue": 89000.25,
        "region": "East",
        "active": False,
        "last_updated": "2024-01-13T09:15:00Z"
    },
    {
        "client_id": 4,
        "client_name": "Client D",
        "revenue": 420000.00,
        "region": "West",
        "active": True,
        "last_updated": "2024-01-16T16:45:00Z"
    },
    {
        "client_id": 5,
        "client_name": "Client E",
        "revenue": 195000.30,
        "region": "Central",
        "active": True,
        "last_updated": "2024-01-12T11:30:00Z"
    }
]

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "BDD Demo Mock API",
        "version": "1.0.0",
        "endpoints": [
            "/clients",
            "/clients/{client_id}",
            "/health",
            "/dashboard"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }

@app.get("/clients")
async def get_clients(active_only: bool = False):
    """Get all clients or only active clients."""
    try:
        clients = SAMPLE_CLIENTS.copy()
        
        if active_only:
            clients = [client for client in clients if client["active"]]
        
        # Add some random variation to revenue for testing
        for client in clients:
            # Add small random variation (±5%)
            variation = random.uniform(-0.05, 0.05)
            client["revenue"] = round(client["revenue"] * (1 + variation), 2)
        
        return {
            "data": clients,
            "count": len(clients),
            "timestamp": datetime.now().isoformat(),
            "filters": {"active_only": active_only}
        }
        
    except Exception as e:
        logger.error(f"Error getting clients: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/clients/{client_id}")
async def get_client(client_id: int):
    """Get specific client by ID."""
    try:
        client = next((c for c in SAMPLE_CLIENTS if c["client_id"] == client_id), None)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Add small random variation to revenue
        client_copy = client.copy()
        variation = random.uniform(-0.05, 0.05)
        client_copy["revenue"] = round(client_copy["revenue"] * (1 + variation), 2)
        
        return {
            "data": client_copy,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple HTML dashboard for UI testing."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>BDD Demo Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .clients-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .client-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background-color: #fafafa;
        }
        .client-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .revenue {
            font-size: 24px;
            font-weight: bold;
            color: #2e7d32;
            margin: 10px 0;
        }
        .region {
            color: #666;
            font-style: italic;
        }
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .active {
            background-color: #c8e6c9;
            color: #2e7d32;
        }
        .inactive {
            background-color: #ffcdd2;
            color: #c62828;
        }
        .refresh-btn {
            background-color: #1976d2;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 20px 0;
        }
        .refresh-btn:hover {
            background-color: #1565c0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BDD Demo Dashboard</h1>
            <p>Client Revenue Overview</p>
            <button class="refresh-btn" onclick="location.reload()">Refresh Data</button>
        </div>
        
        <div class="clients-grid" id="clientsGrid">
            <!-- Clients will be loaded here -->
        </div>
    </div>

    <script>
        async function loadClients() {
            try {
                const response = await fetch('/clients');
                const data = await response.json();
                
                const grid = document.getElementById('clientsGrid');
                grid.innerHTML = '';
                
                data.data.forEach(client => {
                    const card = document.createElement('div');
                    card.className = 'client-card';
                    card.innerHTML = `
                        <div class="client-name">${client.client_name}</div>
                        <div class="revenue">$${client.revenue.toLocaleString()}</div>
                        <div class="region">Region: ${client.region}</div>
                        <div class="status ${client.active ? 'active' : 'inactive'}">
                            ${client.active ? 'Active' : 'Inactive'}
                        </div>
                    `;
                    grid.appendChild(card);
                });
            } catch (error) {
                console.error('Error loading clients:', error);
                document.getElementById('clientsGrid').innerHTML = 
                    '<p style="color: red;">Error loading client data</p>';
            }
        }
        
        // Load clients when page loads
        document.addEventListener('DOMContentLoaded', loadClients);
    </script>
</body>
</html>
    """
    return html_content

@app.get("/api/test-data")
async def get_test_data():
    """Get test data for Great Expectations validation."""
    try:
        # Generate test data with some edge cases for validation
        test_data = []
        
        for i in range(10):
            record = {
                "id": i + 1,
                "name": f"Test Record {i + 1}",
                "value": random.uniform(10, 1000),
                "category": random.choice(["A", "B", "C"]),
                "is_valid": random.choice([True, False]),
                "created_date": datetime.now().isoformat()
            }
            
            # Add some edge cases
            if i == 8:  # Add a record with very high value
                record["value"] = 1500000
            elif i == 9:  # Add a record with negative value
                record["value"] = -100
                
            test_data.append(record)
        
        return {
            "data": test_data,
            "count": len(test_data),
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "purpose": "Great Expectations validation testing",
                "edge_cases": ["high_value", "negative_value"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating test data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def run_server(host: str = "127.0.0.1", port: int = 8001):
    """Run the FastAPI server."""
    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_server()
