# Audited preserved runs for Analyzer v1

This directory contains portable preserved Pegasus run artifacts used
by the Analyzer v1 integration tests.

The source executions were produced on `pegasus-master` under:

    ~/pegasus-lab/pegasus_avance_semana_1_6/experiments

The preserved cases are:

1. process_50mib
2. pipeline_50mib_balanced
3. pipeline_10mib_same
4. pipeline_10mib_balanced
5. pipeline_10mib_cross

The mapping between case names, original relative paths, HTCondor
history snapshots and expected metric values is defined in:

    fixtures/audited/integration_runs.json

HTCondor history evidence is preserved separately in:

    fixtures/audited/history/

These directories are intentionally not byte-for-byte copies of every
runtime sandbox artifact. They preserve the Pegasus/HTCondor artifacts
required to reconstruct and validate Analyzer v1 semantics, including
workflow description, submit descriptions, scientific metadata,
execution-model metadata and configuration.

Scientific payload files, executables, stdout/stderr, transient
sandboxes and unrelated runtime outputs are not duplicated when they
are not required by Analyzer v1.

Integrity hashes for the preserved artifacts are stored in:

    MANIFEST.sha256

The original executions remain the authoritative raw experimental
archive. These copies exist to make Analyzer v1 regression and
integration validation portable and reproducible.

To run the preserved-run integration tests from the repository root:

    export PEGASUS_EXPERIMENTS_ROOT="$PWD/fixtures/audited/runs"

    PEGASUS_RUN_INTEGRATION=1 \
    python3 -m unittest tests.integration.test_preserved_runs -v
