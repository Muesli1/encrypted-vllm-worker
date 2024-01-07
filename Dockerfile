FROM runpod/base:0.4.4-cuda12.1.0

# Python dependencies
COPY builder/requirements.txt /requirements.txt
RUN python3.11 -m pip install --upgrade pip && \
    python3.11 -m pip install --upgrade -r /requirements.txt --no-cache-dir && \
    rm /requirements.txt

# --- System dependencies ---
COPY builder/setup.sh /setup.sh
RUN /bin/bash /setup.sh && \
     rm /setup.sh

# Add src files
ADD src .

CMD python3.11 -u /handler.py
