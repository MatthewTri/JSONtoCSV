import json
import csv
import streamlit as st
from io import StringIO

st.title("Swagger/OpenAPI JSON to CSV")

uploaded_file = st.file_uploader("Upload Swagger JSON file", type=["json"])

if uploaded_file:
    swagger = json.load(uploaded_file)

    schemas = swagger.get("components", {}).get("schemas", {})
    paths = swagger.get("paths", {})

    def resolve_schema(schema):
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            return schemas.get(ref_name, {})
        return schema

    def schema_to_string(schema):
        schema = resolve_schema(schema)
        if "properties" in schema:
            return ", ".join([
                f"{name}: {resolve_schema(info).get('type', 'object')}"
                for name, info in schema["properties"].items()
            ])
        elif "type" in schema and schema["type"] == "array":
            item_schema = resolve_schema(schema.get("items", {}))
            if "properties" in item_schema:
                return "[ " + ", ".join([
                    f"{name}: {resolve_schema(info).get('type', 'object')}"
                    for name, info in item_schema["properties"].items()
                ]) + " ]"
            else:
                return "array of " + item_schema.get("type", "object")
        elif "type" in schema:
            return schema.get("type")
        return ""

    data_rows = []

    for path, methods in paths.items():
        for method, details in methods.items():
            method = method.upper()

            operation_id = details.get("operationId", "")

            # === PAYLOAD ===
            payload = ""
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                for ct in ["application/json", "text/json", "application/*+json"]:
                    if ct in content:
                        payload = schema_to_string(content[ct].get("schema", {}))
                        break

            # === RESPONSE ===
            response = ""
            res_200 = details.get("responses", {}).get("200", {})
            res_content = res_200.get("content", {})
            for ct in ["application/json", "text/json", "text/plain"]:
                if ct in res_content:
                    response = schema_to_string(res_content[ct].get("schema", {}))
                    break

            data_rows.append({
                "Method": method,
                "URL": path,
                "Name": operation_id,
                "Payload": payload,
                "Response": response
            })

    # Tampilkan tabel di Streamlit
    st.success("Berhasil mengurai Swagger JSON!")
    st.dataframe(data_rows)

    # Buat CSV dan tampilkan tombol download
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["Method", "URL", "Name", "Payload", "Response"])
    writer.writeheader()
    writer.writerows(data_rows)
    csv_data = output.getvalue().encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name="swagger_output.csv",
        mime="text/csv"
    )
