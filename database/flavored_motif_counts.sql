CREATE MATERIALIZED VIEW cyberbullying_motifs.flavored_motif_counts AS
SELECT
plain.unit_id,
flavored.node_flavor,
flavored.edge_flavor,
flavored.motif_hash,
count (*) AS hash_count
FROM cyberbullying_motifs.flavored_motifs AS flavored
INNER JOIN cyberbullying_motifs.plain_motifs AS plain
ON flavored.plain_motif_id = plain.plain_motif_id
GROUP BY
plain.unit_id,
flavored.node_flavor,
flavored.edge_flavor,
flavored.motif_hash ;
