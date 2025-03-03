FROM python:3.11-bookworm

WORKDIR /bob

RUN pip3 install --upgrade pip \
    && pip3 install poetry

COPY ./ /bob/

# TODO install `--without dev`
RUN poetry config virtualenvs.create false \
    && poetry lock \
    && poetry install --no-interaction --no-ansi --no-root

RUN chmod +x src/main.py


CMD ["python", "src/main.py"]
