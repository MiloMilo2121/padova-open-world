# Padova Open World

A new Unity 6.3 LTS project using the Universal Render Pipeline. The project starts from Unity's blank Universal 3D template and targets native macOS development.

## Open the project

Install Unity Editor `6000.3.25f1` for Apple silicon and activate a Unity Personal license. From this repository's root, run:

```sh
unity open .
```

The Unity CLI and `com.unity.pipeline` package are configured for local Editor automation. After the Editor finishes importing packages, check the connection with:

```sh
unity pipeline list
unity status
unity command
```

Unity's MCP server is registered in the local Claude Code and Codex user configurations. Start a new agent session after opening the Editor to use the live tools.

## Project data

Commit `Assets/`, `Packages/`, and `ProjectSettings/`, including Unity `.meta` files. `Library/`, `Temp/`, `Logs/`, and other generated files are ignored.

This local project is not linked to Unity Cloud and does not use Cloud Build, Unity Version Control, or paid Unity Gaming Services. The separate Unity Cloud project created in the web interface is not needed for local development.
