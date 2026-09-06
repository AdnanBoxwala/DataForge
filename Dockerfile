# STAGE 1:
FROM python:3.13.15-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config && rm -rf /var/lib/apt/lists/*

# Build the venv at the exact path it will occupy in the final image. A venv is
# not relocatable: console scripts hardcode the interpreter in their shebang, so
# one built at /build/.venv stops working the moment it is copied elsewhere.
# UV_COMPILE_BYTECODE: precompile .pyc at build time. The container is
#   short-lived and imports each module exactly once, so without this every run
#   pays to compile numpy and asammdf on import.
# UV_LINK_MODE: copy rather than hardlink out of the cache mount, which sits on
#   a different filesystem than the target.
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

# Dependencies first: this layer is keyed only on pyproject.toml and uv.lock, so
# editing source does not trigger a reinstall (which would recompile zstd).
RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --no-install-project --no-dev --frozen

# Then the project itself. --no-editable unpacks the package into site-packages
# instead of linking back to /build/src, so the venv is self-contained.
COPY src ./src
RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=README.md,target=README.md \
    uv sync --no-dev --frozen --no-editable

# STAGE 2:
# Using clean base reduces image size from 683 MB to 340 MB
FROM python:3.13.15-slim

# Create an unprivileged user to run as, so files written into
# bind-mounted /work aren't owned by root on the host.
# /work must be created here, while still root: WORKDIR would create it root-owned,
# and after USER the build can no longer chown it. Without this the container
# cannot write its report unless something writable is mounted over /work.
RUN useradd -m -u 1000 dataforge \
    && install -d -o dataforge -g dataforge /work

COPY --from=build --chown=dataforge:dataforge /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /work

USER dataforge

ENTRYPOINT ["dataforge"]
CMD ["--help"]
