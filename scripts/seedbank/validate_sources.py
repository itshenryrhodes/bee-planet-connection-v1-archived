#!/usr/bin/env python3
import json, sys, os
from jsonschema import validate, Draft202012Validator

schema_path = os.path.join("data","research_sources.schema.json")
data_path = os.path.join("data","research_sources.json")

with open(schema_path, encoding="utf-8") as f:
    schema = json.load(f)
with open(data_path, encoding="utf-8") as f:
    data = json.load(f)

errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: e.path)
if errors:
    for e in errors:
        print(str(e.message))
    sys.exit(1)
print("OK")
