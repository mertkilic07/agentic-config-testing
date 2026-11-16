# Reproducible environment for the SQLite configuration experiments.
#
# Build:  docker build -t ens491-sqlite .
# Run:    docker run --rm -it -v "$PWD:/work" ens491-sqlite
#
# The image contains everything that is NOT stored in git:
#   /opt/sqlite-src-3460100   pinned SQLite 3.46.1 source (official archive)
#   /opt/acts/acts.jar        NIST ACTS Basic 1.0 (official NIST download)
# The repository is mounted at /work. Builds and test runs happen inside the
# container's own filesystem (/home/tester/ens491-work), never on the bind mount,
# because file-permission tests do not work on a Mac/Windows bind mount.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        tcl \
        tcl-dev \
        python3 \
        python3-venv \
        lcov \
        unzip \
        default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# gcovr 8.3: gcovr 7.0 from Ubuntu failed with "UnknownLineType" on SQLite's gcov output
RUN python3 -m venv /opt/coverage-env \
    && /opt/coverage-env/bin/pip install --no-cache-dir "gcovr==8.3"
ENV PATH="/opt/coverage-env/bin:${PATH}"

# Pinned SQLite source (version used for every experiment)
RUN curl -fsSL -o /tmp/sqlite.zip https://www.sqlite.org/2024/sqlite-src-3460100.zip \
    && unzip -q /tmp/sqlite.zip -d /opt \
    && rm /tmp/sqlite.zip

# NIST ACTS Basic 1.0 (no constraint support; see models/README.md)
RUN mkdir -p /opt/acts \
    && curl -fsSL -o /opt/acts/acts.jar \
       "https://csrc.nist.gov/csrc/media/Projects/automated-combinatorial-testing-for-software/documents/acts_basic_1.0%203.jar"

# SQLite's Tcl tests refuse to run correctly as root (chmod-based checks)
RUN useradd --create-home --shell /bin/bash tester \
    && chmod -R a+rX /opt/sqlite-src-3460100
USER tester
WORKDIR /work
CMD ["bash"]
