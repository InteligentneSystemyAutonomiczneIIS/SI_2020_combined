#!/bin/bash

docker run --runtime nvidia -it --rm --network host --volume ~/nvdli-data:/nvdli-nano/data --volume /tmp/argus_socket:/tmp/argus_socket --device /dev/video0 --device /dev/ttyTHS1 nvcr.io/nvidia/dli/dli-nano-ai:v2.0.0-r32.4.3

