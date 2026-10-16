from contextjetpack.compiler import compile_message
from contextjetpack.defaults import new_data


def test_compile_message_includes_id_path_reason_and_options():
    data = new_data()
    for document in data["documents"].values():
        document["selected"] = False
    data["purpose"] = "Build a tiny useful thing."
    item = data["documents"]["softspec-v3"]
    item["selected"] = True
    item["designation"] = "required"
    data["options"]["encourage-questions"] = True
    data["options"]["request-ack"] = True

    registry = {
        "softspec.spec.v3": {
            "title": "SoftSpec Specification (v3)",
            "location": [{"path": "C:/docs/softspec.txt"}],
        }
    }

    message = compile_message(data, registry)

    assert "Build a tiny useful thing." in message
    assert "Read now (before you begin):" in message
    assert "Registry ID: softspec.spec.v3" in message
    assert "C:\\docs\\softspec.txt" in message or "C:/docs/softspec.txt" in message
    assert "Please acknowledge" in message
    assert "please ask" in message


def test_compile_message_ignores_unresolved_placeholder():
    data = new_data()
    for key, document in data["documents"].items():
        document["selected"] = key == "reducer-core-architecture"
    message = compile_message(data, {})

    assert "project directory system" not in message
