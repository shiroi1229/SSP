# SSP workspace notes

The upstream README in this directory covers full installation options. For day-to-day work in this repository you usually just need to point the server at the repo root:

```
uvx mcp-server-git --repository d:\\gemini
```

If you prefer Docker, run the image from this directory so the bind mount resolves correctly:

```
docker build -t mcp/git .
docker run --rm -i --mount type=bind,src=d:\\gemini,dst=/workspace mcp/git --repository /workspace
```

Add either command to your MCP client config (Claude Desktop, VS Code `mcp.json`, etc.) and you will be able to run the Git tools (`git_status`, `git_diff_*`, `git_commit`, etc.) against this repo without leaving the assistant.
