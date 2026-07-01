# garak red-team scanner, isolated from the app's modern stack.
#
# Why a container at all: garak (every version available, up to 0.9.0.9) is built
# for the openai v0.x SDK -- 0.9.0.9 even hard-pins `openai>=0.27.7,<1.0.0`, and
# its generators call `openai.error.*`, removed in openai v1. The app requires
# openai >=1.x (via agent-framework), so garak CANNOT live in the app's venv.
# Here it gets its own openai 0.28.x and runs as a sidecar: it scans the model
# endpoint and writes a JSONL report to a mounted volume, which the Safety &
# Trust engine then ingests (`ms-agent-safety --stages garak --garak-report ...`).
#
# Build (from the repo's microsoft_agent_framework_app/ root):
#   docker build -t ms-agent-garak src/ms_agent_app/safety_engine/garak
#
# Run (writes ./runs/garak.report.jsonl on the host):
#   docker run --rm --env-file .env -v ${PWD}/runs:/work/runs ms-agent-garak \
#       --model_type openai --model_name gpt-3.5-turbo \
#       --probes dan,encoding,promptinject --generations 5 \
#       --report_prefix /work/runs/garak
#
# Then on the host:
#   uv run ms-agent-safety --target-provider openai --stages garak \
#       --garak-report runs/garak.report.jsonl --out runs/

FROM python:3.11-slim

# Install the CPU-only torch first so we don't pull the multi-GB CUDA build that
# garak's `torch>=2.1.0` dependency would otherwise drag in.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir "garak==0.9.0.9"

# UTF-8 so garak's report banner (it prints an emoji) never trips a code page.
ENV PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /work
# Invoke via `python -m garak` rather than the `garak` console script -- the
# module entrypoint is always present, whereas the script may not be on PATH.
ENTRYPOINT ["python", "-m", "garak"]
CMD ["--help"]
