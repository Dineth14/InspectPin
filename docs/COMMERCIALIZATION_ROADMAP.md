# From evaluation unit to a field pilot

| Stage | Deliverable | Evidence required to move on |
|---|---|---|
| University evaluation | Freeze the tested LAN build, demonstrate battery-powered label inspection and identify the tested subset of recording features. | Signed physical acceptance sheet, retrievable originals, exported report and a rehearsed fallback. |
| Limited hosted pilot | Deploy one persistent receiver, invite named users, provision unique device credentials, exercise revocation, configure provider limits and a retention/deletion policy. | Laptop-off field test, successful backup restoration, deletion verification, monitored latency and costs for consented inspections. |
| Field validation | Trial the same de-energized inspection with technicians using their existing workflow and the wearable. Collect lighting, legibility, playback, workflow time and battery runtime. | Measured completion and correction rates, documented operator consent, enclosure and battery review, support and service procedure. |
| Production engineering | Factory enrollment, signed update and rollback, distribution signing, tested recovery from power loss, independent security/privacy and hardware conformity review for intended markets. | Tested production units and documented release process, supplier quotations, yield and service cost. |
| Scale after demand | Move accounts/jobs to transactional PostgreSQL, media to access-controlled object storage and work to durable queues; profile bottlenecks before adding replicas. | Load-test results, tenant isolation tests, recovery objectives and cost per successful inspection. |

A pilot pricing hypothesis is hardware sold per unit plus a per-team service plan with metered inference. Estimate the hardware floor from the purchased BOM, assembly, enclosure, yield and support. Estimate the service floor from measured speech compute, provider tokens/images, storage, traffic and support per inspection. No selling price, margin or battery-life promise has been validated.
