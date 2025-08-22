CREATE TABLE repo_docs (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    summary TEXT,
    diagram TEXT
);
