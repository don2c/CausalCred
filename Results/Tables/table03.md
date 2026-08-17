# Table 3: Concrete CausalCred-PQ profile

| Function | Instantiation |
| --- | --- |
| Issuer, attester, monitor, root signatures | ML-DSA-65 |
| Authority collusion resistance | independent t_Y-of-n_Y ML-DSA signatures |
| Task channel / optional capability key | ML-KEM-768 + KMAC256 KDF |
| Commitments and event chain | SHAKE256 with 384-bit output, domain-separated |
| Attributes and revocation | SHAKE256/384 Merkle / sparse-Merkle trees |
| Scoped pseudonym | T_c = KMAC256_zα("nym" \|\| c) |
| Proof system | Ligetron transparent post-quantum ZK-SNARK |
| Symmetric action authentication | KMAC256, optional profile only |
