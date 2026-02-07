# Connex OpenAGI Desktop App

This project uses [Tauri](https://tauri.app/) to wrap the Next.js web application into a lightweight, native desktop app.

## Prerequisites

1.  **Node.js**: Ensure you have Node.js installed.
2.  **Rust**: Install Rust (required for Tauri).
    ```bash
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```
3.  **System Dependencies**:
    -   **macOS**: Needs Xcode Command Line Tools (`xcode-select --install`).
    -   **Linux**: Needs webkit2gtk (see Tauri docs).
    -   **Windows**: Needs C++ Build Tools and WebView2.

## Setup

1.  Install dependencies:
    ```bash
    cd ui
    npm install
    ```

2.  Run in Desktop Development Mode:
    ```bash
    npm run tauri dev
    ```
    This will start the Next.js server and open a native window.

## Building for Production

To create a standalone executable (DMG, AppImage, or MSI):

```bash
cd ui
npm run tauri build
```

The output binary will be located in `ui/src-tauri/target/release/bundle/`.

## Troubleshooting

-   **"Error: failed to run tauri build"**: Ensure you have run `npm install` to get the Tauri CLI.
-   **Window is blank**: Check if the Next.js export is successful (`npm run build`).
