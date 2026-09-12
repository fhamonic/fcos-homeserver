# `openwebui`

Configuration for [Open WebUI](https://openwebui.com/), a chat interface for large language models served by Ollama or any OpenAI-compatible API (for instance a vLLM instance on another machine of the network). The template deploys the single container with a named volume for its data; the model backends are configured from the web interface.

The first account created from the web interface becomes the administrator.

## `openwebui.image`

The image of Open WebUI to deploy.

* **Type:** String
* **Example:** `ghcr.io/open-webui/open-webui:main`

## `openwebui.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3009`
