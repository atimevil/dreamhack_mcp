# Dreamhack MCP Server

This project implements a Model Context Protocol (MCP) server using the fastmcp library to interact with the Dreamhack wargame platform. It provides tools and resources to automate tasks such as fetching problem lists, downloading challenge files, and deploying them locally.

## Features

-   Dreamhack login
-   Fetch a list of all web problems
-   Fetch web problems filtered by difficulty
-   Download challenge files for a specific problem, including automatic extraction of zip files
-   Deploy downloaded challenges using Docker or by running `app.py`
-   Stop running deployed challenges

## Installation Requirements

-   Python 3.10 or higher
-   pip (Python package installer)
-   git (required to install fastmcp from GitHub)
-   Docker (optional, required for deploying challenges via Docker)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace with your repository URL
    cd <repository_directory> # Replace with your repository directory
    ```

2.  **Install dependencies:**
    Make sure you have Python 3.10+ and pip installed. Then, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: fastmcp is installed directly from its GitHub repository as it's not on PyPI.)*

## Usage

### Running the Server Locally

You can run the fastmcp server directly as a Python script. The server will listen for incoming MCP requests over HTTP.

```bash
python server.py
```

By default, the server listens on `http://127.0.0.1:8000/mcp`. You can configure the host, port, and MCP path using environment variables:

-   `HOST`: The host to bind to (default: `127.0.0.1`)
-   `PORT`: The port to listen on (default: `8000`)
-   `MCP_PATH`: The path prefix for MCP endpoints (default: `/mcp`)

Example using environment variables:

```bash
HOST=0.0.0.0 PORT=8080 python server.py
```
*(Note: On Windows, setting environment variables might require a different syntax, e.g., `set HOST=0.0.0.0 && set PORT=8080 && python server.py`)*

### Testing with MCP Inspector

You can use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to test the server's tools, prompts, and resources visually.

1.  Make sure the `server.py` is running (as shown above).
2.  Open a new terminal and run MCP Inspector:
    ```bash
    npx @modelcontextprotocol/inspector
    ```
3.  In the Inspector UI, select **Transport Type: `streamable-http`** and enter the **Server URL:** `http://localhost:8000/mcp` (or the address you configured if using environment variables).
4.  Click **Connect**. You should now see the available tools, prompts, and resources from your server.

### Using with Other MCP Clients

This server can be integrated with any MCP-compatible client, such as AI coding assistants (like Cursor) or custom applications, by configuring the client to connect to the server's URL (`http://<host>:<port>/mcp`).

## Deployment on Smithery.ai

This repository includes the necessary configuration files for deployment on Smithery.ai:

-   `Dockerfile`: Defines the container image build process, ensuring all dependencies (including git) are installed.
-   `smithery.yaml`: Configures Smithery.ai to build the Docker image and run the server as an HTTP-based MCP agent, exposing necessary ports and setting environment variables. It also defines the server's `configSchema`.

Follow the Smithery.ai documentation for deploying an agent from a GitHub repository. The platform will use these files to build and run your server.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
