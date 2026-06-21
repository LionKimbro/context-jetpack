DOCUMENTS = [
    {
        "key": "general-background",
        "label": "General background",
        "document-id": "lions_dictionary_for_llms",
        "reason": "Read this for high-level orientation to Lion's recurring concepts, systems, and vocabulary.",
    },
    {
        "key": "project-directory-system",
        "label": "Lion's project directory system",
        "document-id": "",
        "reason": "Read this for a brief overview of how Lion's projects and repositories are organized.",
    },
    {
        "key": "programming-guidelines",
        "label": "Programming guidelines",
        "document-id": "lionsphilosophyofprogramming.2025.simplified",
        "reason": "Read this before programming so the implementation follows Lion's preferred style and conventions.",
    },
    {
        "key": "lionscliapp",
        "label": "lionscliapp reference",
        "document-id": "lionscliapp.reference.v1",
        "reason": "Read this when building a Python CLI application with Lion's standard application framework.",
    },
    {
        "key": "machine-root",
        "label": "Machine Root package",
        "document-id": "machine-root.package.description.v1",
        "reason": "Read this when the application needs to resolve named machine-local resources through Machine Root.",
    },
    {
        "key": "json-document-writing",
        "label": "JSON documentation-writing guide",
        "document-id": "lions-docs.description.json-document-format-for-llms.v1",
        "reason": "Read this when writing JSON documents intended for Lion's systems or for LLM consumption.",
    },
    {
        "key": "softspec",
        "label": "SoftSpec v2",
        "document-id": "softspec.spec.v2",
        "reason": "Read this when specifying data structures in JSON documents; SoftSpec is the preferred approach.",
    },
    {
        "key": "m1-core",
        "label": "M1 Lattice core specification",
        "document-id": "m1lattice.spec.core.v2",
        "reason": "Read this for the core structure and behavior of M1 entities and aspects.",
    },
    {
        "key": "m1-transport",
        "label": "M1 Lattice transport specification",
        "document-id": "m1lattice.spec.transport.v2",
        "reason": "Read this when storing or exchanging M1 entities and aspects.",
    },
    {
        "key": "m1-link-types",
        "label": "M1 recommended link types",
        "document-id": "m1lattice.vocab.linktypes.v1",
        "reason": "Read this when choosing link types for relationships in M1 data.",
    },
    {
        "key": "m1-merging",
        "label": "M1 merging guide",
        "document-id": "m1lattice.merging.guide.v2",
        "reason": "Read this when combining M1 transport units or reasoning about merge behavior.",
    },
    {
        "key": "m1-runtime",
        "label": "M1 runtime manual",
        "document-id": "m1lattice.runtime-manual",
        "reason": "Read this when implementing or using the M1 runtime.",
    },
]


def new_data():
    return {
        "purpose": "",
        "options": {
            "encourage-questions": False,
            "request-ack": False,
        },
        "documents": {
            item["key"]: {
                "selected": False,
                "designation": "recommended",
                "reason": item["reason"],
            }
            for item in DOCUMENTS
        },
    }
