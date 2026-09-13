# `convertx`

Configuration for [ConvertX](https://github.com/C4illin/ConvertX), a self-hosted file converter that wraps FFmpeg, ImageMagick, LibreOffice, Pandoc, Calibre, Inkscape and a dozen other tools behind one web page: upload files, pick a target format, download the results. The template deploys the single container with a named volume for its database and the converted files, and generates once the secret that signs the login sessions, so that they survive restarts. Publish it through a [caddy](caddy.md) site, as the application refuses logins over plain HTTP from anywhere but `localhost`.

The first account is created from the web interface, and registration is closed afterwards. Converted files are deleted after 24 hours.

!!! note
    Anyone who reaches the page before you can register the first account and become its only user. Create your account right after the first start, or keep the Caddy site restricted to the LAN until then.

## `convertx.image`

The image of ConvertX to deploy. The project publishes only exact version tags (`v0.18.0`) next to `latest` and `main`, so updating means bumping the tag.

* **Type:** String
* **Example:** `ghcr.io/c4illin/convertx:v0.18.0`

## `convertx.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3018`
