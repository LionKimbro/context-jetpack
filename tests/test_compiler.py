from contextjetpack.compiler import compile_message
from contextjetpack.defaults import new_data


def test_compile_message_includes_id_path_reason_and_options():
    data = new_data()
    data["purpose"] = "Build a tiny useful thing."
    item = data["documents"]["softspec"]
    item["selected"] = True
    item["designation"] = "required"
    data["options"]["encourage-questions"] = True
    data["options"]["request-ack"] = True

    registry = {
        "softspec.spec.v2": {
            "title": "SoftSpec Specification (v2)",
            "location": [{"path": "C:/docs/softspec.txt"}],
        }
    }

    message = compile_message(data, registry)

    assert "Build a tiny useful thing." in message
    assert "Required reading:" in message
    assert "Registry ID: softspec.spec.v2" in message
    assert "C:\\docs\\softspec.txt" in message or "C:/docs/softspec.txt" in message
    assert "Please acknowledge" in message
    assert "please ask" in message


def test_compile_message_rejects_unresolved_selected_document():
    data = new_data()
    data["documents"]["project-directory-system"]["selected"] = True

    try:
        compile_message(data, {})
    except ValueError as exc:
        assert "no Librarian document ID" in str(exc)
    else:
        raise AssertionError("expected ValueError")
