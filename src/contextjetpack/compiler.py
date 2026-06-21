from .defaults import DOCUMENTS
from .registry import resolve_document


def compile_message(data, registry_entries):
    purpose = data["purpose"].strip()
    if not purpose:
        purpose = "(No project purpose has been supplied yet.)"

    selected = {"required": [], "recommended": []}
    for definition in DOCUMENTS:
        state = data["documents"][definition["key"]]
        if not state["selected"]:
            continue
        document_id = definition["document-id"]
        if not document_id:
            raise ValueError(
                f"{definition['label']} has no Librarian document ID yet"
            )
        resolved = resolve_document(registry_entries, document_id)
        resolved["reason"] = state["reason"].strip()
        selected[state["designation"]].append(resolved)

    lines = [
        "We are making the following application:",
        "",
        purpose,
        "",
        "Before beginning, consult the following reference documents. "
        "Each coordinate includes both its Librarian registry ID and its resolved full path.",
    ]

    for designation, heading in (
        ("required", "Required reading"),
        ("recommended", "Recommended reading"),
    ):
        documents = selected[designation]
        if not documents:
            continue
        lines.extend(["", f"{heading}:"])
        for document in documents:
            lines.extend(
                [
                    "",
                    f"- {document['title']}",
                    f"  Registry ID: {document['document-id']}",
                    f"  Path: {document['path']}",
                    f"  Why: {document['reason'] or 'No additional reason supplied.'}",
                ]
            )

    if not selected["required"] and not selected["recommended"]:
        lines.extend(["", "No reference documents were selected."])

    if data["options"]["request-ack"]:
        lines.extend(
            [
                "",
                "Please acknowledge which of these documents you read before beginning implementation.",
            ]
        )
    if data["options"]["encourage-questions"]:
        lines.extend(
            [
                "",
                "If you have questions or find important ambiguities, please ask before making consequential assumptions.",
            ]
        )

    return "\n".join(lines).strip() + "\n"
