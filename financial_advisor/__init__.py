# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Financial coordinator: provide reasonable investment strategies"""

import os

import google.auth

from . import agent  # noqa: F401

import json
import tempfile

# Railway Fix: If credentials are passsed as JSON content, save to a temp file
gac = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if gac and gac.strip().startswith("{"):
    print("Detected JSON in GOOGLE_APPLICATION_CREDENTIALS. Writing to temp file...")
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write(gac)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
    print(f"Credentials saved to {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

try:
    _, project_id = google.auth.default()
except Exception as e:
    print(f"Error loading credentials: {e}")
    # Fallback/Debugging
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
