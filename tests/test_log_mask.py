"""A secret's value masked in a task's log (docs/specs/168 I1): in plain words, in a URL, in a JSON line; a short or empty secret masks nothing; the values are found where the Board keeps them."""
from __future__ import annotations

import json

from orkboard.realm import idea_secrets, log_mask
from orkboard.realm.log_mask import MASK, mask

KEY = "sk-live-9f3A/b+c=Zq7"


def test_a_value_in_plain_text_is_masked_wherever_it_stands():
    out = mask(f"export TOKEN={KEY}\nthen {KEY} again, and {KEY}.", [KEY])
    assert KEY not in out and out.count(MASK) == 3 and out.startswith(f"export TOKEN={MASK}\n")


def test_a_value_in_a_url_is_masked_as_it_was_encoded():
    for stand in (KEY, "sk-live-9f3A%2Fb%2Bc%3DZq7", "sk-live-9f3A%2fb%2bc%3dZq7"):
        out = mask(f"GET https://api.x.io/v1?key={stand}&x=1", [KEY])
        assert stand not in out and out == f"GET https://api.x.io/v1?key={MASK}&x=1", stand


def test_a_value_in_a_json_line_is_masked_as_json_wrote_it():
    value = 'pa"ss\nwörd-123'
    line = json.dumps({"password": value, "ok": True})
    assert value not in line and mask(line, [value]) == '{"password": "%s", "ok": true}' % MASK
    assert mask(json.dumps({"p": value}, ensure_ascii=False), [value]) == '{"p": "%s"}' % MASK
    assert mask("q=two+words+here", ["two words here"]) == f"q={MASK}"                  # a space as a form posts it


def test_a_short_or_empty_secret_does_not_mask_everything():
    text = "the quick brown fox 12 jumps over a lazy dog"
    for value in ("", " ", "a", "12", "fox", None, 7):
        assert mask(text, [value]) == text, repr(value)
    assert mask(text, []) == text and mask("", [KEY]) == ""
    assert mask(text, ["", "quick"]) == text.replace("quick", MASK)        # a good one beside an empty one still masks


def test_the_longer_value_goes_first_so_one_holding_another_is_hidden_whole():
    assert mask("a=abcd-efgh-ijkl b=abcd", ["abcd", "abcd-efgh-ijkl"]) == f"a={MASK} b={MASK}"


def test_dotenv_values_are_those_named_like_a_secret():
    text = "# c\nAPI_KEY=abc12345\nexport DB_PASSWORD='p w 1234'\nPORT=8080\nTOKEN=xyz98765 # note\nNAME=bob\n"
    assert log_mask.dotenv_values(text) == ["abc12345", "p w 1234", "xyz98765"]
    assert log_mask.environ_values({"PATH": "/bin", "GH_TOKEN": "ghp_abcdef", "ORKCRAFT_TASK": "t1", "N": 3}) == ["ghp_abcdef"]


def test_known_reads_the_goals_secrets_the_dotenv_and_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ORKCRAFT_LOGINS_FILE", str(tmp_path / "logins.json"))      # the tests keep the OS keychain out
    repo = tmp_path / "repo"
    state = repo / ".orkcraft"
    repo.mkdir()
    idea_secrets.put(state, "pay", "k1", "whsec_from_the_keychain")
    (repo / ".env").write_text("STRIPE_KEY=sk_test_in_dotenv\nHOST=localhost\n", encoding="utf-8")
    plan = {"todos": [{"id": "k1", "kind": "secret", "title": "WEBHOOK_SECRET"}, {"id": "k2", "kind": "choice", "title": "x"}]}
    got = log_mask.known(state, repo, "pay", plan, environ={"HOME": "/root", "AWS_SECRET": "aws-secret-value"})
    assert set(got) == {"whsec_from_the_keychain", "sk_test_in_dotenv", "aws-secret-value"}
    assert log_mask.known(state, repo, "pay", None, environ={}) == ["sk_test_in_dotenv"]
