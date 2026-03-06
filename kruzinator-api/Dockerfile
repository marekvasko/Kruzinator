FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim
# Copy the project into the image
COPY . /app
# Disable development dependencies
ARG UV_NO_DEV=true
ARG UV_COMPILE_BYTECODE=true
ENV UV_NO_DEV=${UV_NO_DEV}
ENV UV_COMPILE_BYTECODE=${UV_COMPILE_BYTECODE}
# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked
CMD ["uv", "run", "kruzinator-api"]

