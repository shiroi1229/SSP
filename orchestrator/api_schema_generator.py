# path: orchestrator/api_schema_generator.py
# version: v1
# Generates an OpenAPI schema from the FastAPI app and saves it to a JSON file.

import json
import os
import sys
from pathlib import Path

# Add project root to Python path to allow importing 'backend'
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.main import app

def generate_schema():
    """
    Generates a simplified, custom OpenAPI schema from the FastAPI app
    and saves it to data/schemas/openapi.json.
    """
    print("Generating API schema...")
    
    # Ensure the output directory exists
    output_dir = project_root / "data" / "schemas"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "openapi.json"

    # Get the standard OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    simplified_schema = []

    # Process paths and components
    paths = openapi_schema.get("paths", {})
    components = openapi_schema.get("components", {}).get("schemas", {})

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            endpoint_id = operation.get("operationId", f"{method}_{path}".replace("/", "_"))
            
            # --- Input Schema ---
            input_schema = None
            request_body = operation.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                if "application/json" in content:
                    schema_ref = content["application/json"]["schema"].get("$ref")
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                        input_schema = components.get(schema_name, {})

            # --- Output Schema ---
            output_schema = None
            responses = operation.get("responses", {})
            if "200" in responses:
                content = responses["200"].get("content", {})
                if "application/json" in content:
                    schema_ref = content["application/json"]["schema"].get("$ref")
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                        output_schema = components.get(schema_name, {})

            simplified_schema.append({
                "id": endpoint_id,
                "path": path,
                "method": method.upper(),
                "summary": operation.get("summary", ""),
                "tags": operation.get("tags", []),
                "input_schema": input_schema,
                "output_schema": output_schema,
            })

    # Write the simplified schema to the file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(simplified_schema, f, ensure_ascii=False, indent=2)
        print(f"✅ Successfully generated and saved schema to {output_path}")
    except IOError as e:
        print(f"❌ Error writing schema file: {e}")

if __name__ == "__main__":
    generate_schema()
