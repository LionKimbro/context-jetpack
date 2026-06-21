from contextjetpack.storage import load_data, save_data


def test_data_round_trip(tmp_path):
    path = tmp_path / "data.json"
    data = load_data(path)
    data["purpose"] = "Remember me"
    data["documents"]["machine-root"]["selected"] = True
    data["documents"]["machine-root"]["designation"] = "required"

    save_data(path, data)
    loaded = load_data(path)

    assert loaded["purpose"] == "Remember me"
    assert loaded["documents"]["machine-root"]["selected"] is True
    assert loaded["documents"]["machine-root"]["designation"] == "required"
