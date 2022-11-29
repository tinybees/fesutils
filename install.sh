#!/usr/bin/env bash
mkdir -p ~/virtual/fesutils
python3 -m venv ~/virtual/fesutils
~/virtual/fesutils/bin/pip install -U pip==20.2.4
~/virtual/fesutils/bin/pip install wheel
~/virtual/fesutils/bin/pip install -r requirements.txt
