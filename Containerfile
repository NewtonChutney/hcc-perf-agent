# HCC Perf Agent web UI. Built by .github/workflows/image.yaml and pushed to GHCR;
# rdu3 doesn't allow in-cluster builds, so it imports the image (deploy/base/imagestream.yaml).
FROM registry.access.redhat.com/ubi9/python-312

COPY requirements.txt /opt/app-root/src/
RUN pip install --no-cache-dir -r /opt/app-root/src/requirements.txt
COPY agent/ /opt/app-root/src/agent/

# Listens on localhost only: the oauth-proxy sidecar is the sole entry point and sets the
# X-Forwarded-User/Email headers the app trusts.
EXPOSE 8000
CMD ["uvicorn", "agent.web.app:app", "--host", "127.0.0.1", "--port", "8000"]
