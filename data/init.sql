CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS network_nodes (
    node_id BIGINT PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(Point, 4326) NOT NULL,
    street_count INTEGER
);
CREATE TABLE IF NOT EXISTS network_edges (
    from_node BIGINT NOT NULL,
    to_node BIGINT NOT NULL,
    geometry GEOMETRY(LineString, 4326) NOT NULL,
    length DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (from_node, to_node),
    FOREIGN KEY (from_node) REFERENCES network_nodes(node_id),
    FOREIGN KEY (to_node) REFERENCES network_nodes(node_id)
);

CREATE TABLE IF NOT EXISTS network_hospitals (
    hospital_id BIGINT PRIMARY KEY,
    geometry GEOMETRY(Point, 4326) NOT NULL
);


-- TODO: Add indexes