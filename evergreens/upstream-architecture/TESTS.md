<!-- EXAMPLE: Test commands and thresholds shown here are illustrative.
     Customize for your actual service endpoints and expected values.
     Commands use placeholder values (marked with < >) that must be replaced
     with your deployment-specific values before running. See .memory_env
     and your local config for actual values. -->

# Upstream Architecture - Tests

## Smoke Tests (run every cycle)
| ID | Test | Command | Expected |
|----|------|---------|----------|
| S01 | Node version matches | `node --version` | vXX.X.X | <!-- CUSTOMIZE: your Node version -->
| S02 | OpenClaw config exists | `test -f ~/.openclaw/openclaw.json && echo OK` | OK |
| S03 | Models config exists | `test -f ~/.openclaw/agents/main/agent/models.json && echo OK` | OK |
| S04 | Search API reachable (optional) | `curl -s -o /dev/null -w "%{http_code}" https://<your-search-endpoint>/search -X POST -H "Content-Type: application/json" -d '{"q":"test"}'` | 200 | <!-- OPTIONAL: Skip if you don't self-host a search API (e.g. Serper clone) — see GLOSSARY.md "Serper Clone" entry. DELETE this row if not applicable. -->
| S05 | Local models available | `ollama list \| wc -l` | ≥ 1 | <!-- CUSTOMIZE: add grep for your specific model names if desired -->
| S06 | Requirements up to date | `pip list --outdated \| grep -c ""` | Low count |
| S07 | Qdrant collections exist | `curl -s http://localhost:6333/collections \| python3 -m json.tool` | Both collections listed |

## Regression Tests (run after changes)
| ID | Test | Trigger | Command | Expected |
|----|------|---------|---------|----------|
| R01 | Primary model responds | After model config change | `ollama run <your-model> "say ok"` | Contains "ok" | <!-- CUSTOMIZE: your primary model name -->
| R02 | Search API works (optional) | After network change | Search query returns results | JSON with organic array | <!-- OPTIONAL: Only if you self-host a search API. DELETE this row otherwise. -->
| R03 | OpenClaw agent session works | After OpenClaw update | `openclaw agent --message "say hello" --timeout 30 --json` | Valid JSON response |
| R04 | Memory scripts import cleanly | After dependency update | `python3 -c "import qdrant_client, redis"` | No errors |

## Integration Tests (run periodically)
| ID | Test | Frequency | Command | Expected |
|----|------|-----------|---------|----------|
| I01 | All expected models available | Weekly | `ollama list` | All configured models present | <!-- CUSTOMIZE: your expected model count -->
| I02 | Remote GPU reachable (optional) | Weekly | `OLLAMA_HOST=http://<your-gpu-host>:<port> ollama list \| wc -l` | ≥ 1 models | <!-- CUSTOMIZE: your GPU host, or remove if not applicable -->
| I03 | Upstream repo accessible | Weekly | `curl -s -o /dev/null -w "%{http_code}" https://github.com/openclaw` | 200 |
| I04 | Dependency versions match requirements.txt | Weekly | `pip check` | No broken requirements |

## Research Topics
<!-- CUSTOMIZE: Add your own research topics. Examples: -->
- [ ] Evaluate switching memory operations to local/remote GPU vs cloud for cost/privacy tradeoffs
- [ ] Assess which local models could replace cloud calls for curation and coding tasks
- [ ] Track upstream release cadence to optimize check frequency

## Safety Tests (run on security changes)
| ID | Test | Trigger | Command | Expected |
|----|------|---------|---------|----------|
| (none for this evergreen) |

---

*Last updated: 2009-01-03*