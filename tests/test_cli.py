import json

from notrain.cli import main

FIXTURE = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n"


def test_cli_check_file(tmp_path, capsys):
    f = tmp_path / "robots.txt"
    f.write_text(FIXTURE)
    assert main(["check", str(f)]) == 0
    out = capsys.readouterr().out
    assert "GPTBot" in out and "blocked" in out
    assert "PerplexityBot" in out and "allowed" in out


def test_cli_check_json(tmp_path, capsys):
    f = tmp_path / "robots.txt"
    f.write_text(FIXTURE)
    assert main(["check", str(f), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    by_token = {d["token"]: d for d in data}
    assert by_token["GPTBot"]["allowed"] is False
    assert by_token["GPTBot"]["matched_rule"] == "Disallow: /"


def test_cli_check_missing_file(capsys):
    assert main(["check", "/nonexistent/robots.txt"]) == 2


def test_cli_generate(capsys):
    assert main(["generate", "--block", "training",
                 "--allow", "search"]) == 0
    out = capsys.readouterr().out
    assert "User-agent: GPTBot" in out
    assert "Disallow: /" in out


def test_cli_generate_bad_classification():
    assert main(["generate", "--block", "bogus"]) == 2


def test_cli_verify_local_server(local_server, capsys):
    assert main(["verify", local_server]) == 0
    out = capsys.readouterr().out
    assert "GPTBot" in out and "agrees" in out
    assert "MISMATCH" in out  # Bytespider: robots allows, server 403s


def test_cli_monitor_local_server(local_server, tmp_path, capsys):
    store = str(tmp_path / "snaps")
    assert main(["monitor", local_server, "--store", store]) == 0
    out1 = capsys.readouterr().out
    assert "first snapshot" in out1
    assert main(["monitor", local_server, "--store", store]) == 0
    out2 = capsys.readouterr().out
    assert "verdict changes: none" in out2
