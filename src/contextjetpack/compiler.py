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
            continue
        resolved = resolve_document(registry_entries, document_id)
        resolved["reason"] = state["reason"].strip()
        selected[state["designation"]].append(resolved)

    lines = [
        "We are making the following application:",
        "",
        purpose,
        "",
        "Below are reference documents, grouped by when to read them. "
        "Each entry includes both its Librarian registry ID and its resolved full path.",
    ]

    for designation, heading, blurb in (
        ("required", "Read now (before you begin)", None),
        (
            "recommended",
            "Read when relevant (do not read these yet)",
            "Note that these exist and what each one covers, but do not read them now. "
            "Open a document only when you are about to do work that requires its knowledge.",
        ),
    ):
        documents = selected[designation]
        if not documents:
            continue
        lines.extend(["", f"{heading}:"])
        if blurb:
            lines.append(blurb)
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
