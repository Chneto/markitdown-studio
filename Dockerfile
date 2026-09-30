FROM python:3.13-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV EXIFTOOL_PATH=/usr/bin/exiftool
ENV FFMPEG_PATH=/usr/bin/ffmpeg

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    exiftool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip --no-cache-dir install -e /app/packages/markitdown[all] || pip --no-cache-dir install eel bottle rapidocr-onnxruntime opencv-python pydub speechrecognition

EXPOSE 8080

ENTRYPOINT [ "python", "-m", "studio.app" ]
