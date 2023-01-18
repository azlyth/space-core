VERSION 0.6

FROM scratch

python-base:
    FROM DOCKERFILE python

python-image:
    FROM +python-base
    SAVE IMAGE space-core-python

python-test:
    FROM +python-base
    RUN --no-cache python parse.py .