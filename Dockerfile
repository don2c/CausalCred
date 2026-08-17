FROM python:3.11.9-slim-bookworm

WORKDIR /evaluation
COPY . .
ENV PYTHONPATH=/evaluation/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_DATE_EPOCH=1786966469
CMD ["sh", "-c", "python -m causalcred_eval reproduce --root . && python -m unittest discover -s tests -v && python -m causalcred_eval verify --root ."]
