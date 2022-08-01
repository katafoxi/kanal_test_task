# pull official base image
FROM python:3.9.13-bullseye AS base


FROM base AS python-deps

# Setup env
ENV LANG="C.UTF-8" \
    LC_ALL="C.UTF-8" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Install python dependencies in /.venv
COPY ../arch/Pipfile .
COPY ../arch/Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy



FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Install application into container
COPY --chown=appuser . .

# Run the application
#ENTRYPOINT ["python", "-m", "http.server"]
CMD ["python", "main_script.py"]
#CMD ["--directory", "directory", "8000"]
