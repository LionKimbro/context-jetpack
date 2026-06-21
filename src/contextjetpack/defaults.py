DOCUMENTS = [
    {
        "key": "general-background",
        "label": "General background",
        "document-id": "lions_dictionary_for_llms",
        "selected": False,
        "designation": "required",
        "reason": "Read this for high-level orientation to Lion's recurring concepts, systems, and vocabulary.",
    },
    {
        "key": "project-directory-system",
        "label": "Lion's project directory system",
        "document-id": "",
        "selected": True,
        "designation": "required",
        "reason": "Read this for a brief overview of how Lion's projects and repositories are organized.",
    },
    {
        "key": "tkinter-conventions",
        "label": "Conventions for tkinter applications",
        "document-id": "",
        "selected": False,
        "designation": "required",
        "reason": "When you write tkinter user interfaces, follow these guidelines.",
    },
    {
        "key": "programming-guidelines",
        "label": "Programming guidelines",
        "document-id": "lionsphilosophyofprogramming.2025.simplified",
        "selected": True,
        "designation": "required",
        "reason": "These are the programming guidelines that you shall implement the program with.",
    },
    {
        "key": "lionscliapp",
        "label": "lionscliapp reference",
        "document-id": "lionscliapp.reference.v1",
        "selected": False,
        "designation": "required",
        "reason": "The program you are implementing will be built with the lionscliapp framework. Read this so that you know how to use it.",
    },
    {
        "key": "machine-root",
        "label": "Machine Root package",
        "document-id": "machine-root.package.description.v1",
        "selected": False,
        "designation": "required",
        "reason": "Read this when the application needs to resolve named machine-local resources through Machine Root.",
    },
    {
        "key": "json-document-writing",
        "label": "JSON documentation-writing guide",
        "document-id": "lions-docs.description.json-document-format-for-llms.v1",
        "selected": True,
        "designation": "recommended",
        "reason": "Read this when writing JSON documents intended for Lion's systems or for LLM consumption.",
    },
    {
        "key": "softspec",
        "label": "SoftSpec v2",
        "document-id": "softspec.spec.v2",
        "selected": True,
        "designation": "recommended",
        "reason": "Read this when specifying data structures in JSON documents; SoftSpec is the preferred approach.",
    },
    {
        "key": "m1-core",
        "label": "M1 Lattice core specification",
        "document-id": "m1lattice.spec.core.v2",
        "selected": False,
        "designation": "required",
        "reason": "You are going to be handling M1 data. Read this so that you understand the core structure and behavior of M1 entities and aspects.",
    },
    {
        "key": "m1-transport",
        "label": "M1 Lattice transport specification",
        "document-id": "m1lattice.spec.transport.v2",
        "selected": False,
        "designation": "required",
        "reason": "You are going to be storing or exchanging M1 data. Read this so that you understand its transport representation.",
    },
    {
        "key": "m1-link-types",
        "label": "M1 recommended link types",
        "document-id": "m1lattice.vocab.linktypes.v1",
        "selected": False,
        "designation": "required",
        "reason": "Read this when choosing link types for relationships in M1 data.",
    },
    {
        "key": "m1-merging",
        "label": "M1 merging guide",
        "document-id": "m1lattice.merging.guide.v2",
        "selected": False,
        "designation": "required",
        "reason": "Read this when combining M1 transport units or reasoning about merge behavior.",
    },
    {
        "key": "m1-runtime",
        "label": "M1 runtime manual",
        "document-id": "m1lattice.runtime-manual",
        "selected": False,
        "designation": "required",
        "reason": "Read this so that you know how to use the M1 runtime.",
    },
]


def new_data():
    return {
        "purpose": "",
        "options": {
            "encourage-questions": False,
            "request-ack": True,
        },
        "documents": {
            item["key"]: {
                "selected": item["selected"],
                "designation": item["designation"],
                "reason": item["reason"],
            }
            for item in DOCUMENTS
        },
    }
