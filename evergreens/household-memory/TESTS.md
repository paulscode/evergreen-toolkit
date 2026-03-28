<!-- EXAMPLE: Test commands shown here are illustrative.
     Customize for your actual service endpoints and configuration.
     CUSTOMIZE: Replace <agent> in S02 with your QDRANT_COLLECTION name.
     Commands use placeholder values (marked with < >) that must be replaced
     with your deployment-specific values before running. See .memory_env
     and your local config for actual values. -->

# Household Memory - Tests

## Smoke Tests (run every cycle)
| ID | Test | Command | Expected |
|----|------|---------|----------|
| S01 | Redis reachable | `redis-cli ping 2>/dev/null \|\| echo "Redis not running"` | PONG |
| S02 | Qdrant reachable | `curl -s localhost:6333/collections/<agent>-memories 2>/dev/null \|\| echo "Qdrant not running"` | JSON with collection info |
| S03 | Memory directory exists | `test -d memory && echo OK` | OK |
| S04 | Memory env loaded | `test -f .memory_env && echo OK` | OK |

## Regression Tests (run after changes)
| ID | Test | Trigger | Command | Expected |
|----|------|---------|---------|----------|
| R01 | Memory save works | After memory code change | `source .venv/bin/activate && source .memory_env && python3 memory/scripts/save_mem.py --user-id test 2>&1` | Success message or saved confirmation |
| R02 | Memory search works | After Qdrant change | `python3 memory/scripts/search_memories.py "test" --user-id test 2>&1` | JSON results (may be empty) |
| R03 | Daily file created | After save | `ls memory/test/$(date +%Y-%m-%d).md 2>/dev/null && echo OK` | OK (after R01) |

## Integration Tests (run periodically)
| ID | Test | Frequency | Command | Expected |
|----|------|-----------|---------|----------|
| I01 | Full memory cycle | Weekly | Save → File → Search | Both layers work end-to-end |
| I02 | Redis buffer flush | Monthly | Verify buffer clears after save | Buffer empty after save |

## Safety Tests (run on security changes)
| ID | Test | Trigger | Command | Expected |
|----|------|---------|---------|----------|
| F01 | User isolation | After memory code change | Search as `<user1>`, verify can't see `<user2>`'s memories | No cross-user leakage |
| F02 | No sensitive data in logs | After logging change | Check logs for API keys, passwords | None found |

---

*Last updated: 2009-01-02*