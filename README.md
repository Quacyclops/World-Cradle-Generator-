# 🌌 World Cradle: Deterministic Lore Bible Generator

World Cradle is a high-performance, structurally verified worldbuilding engine built for speculative fiction authors, game designers, and creative directors. The system takes raw narrative concepts and expands them into comprehensive, multi-layered fictional settings while enforcing structural integrity, linguistic rules/naming conventions, and aesthetic themes.

By matching the **OpenAI Structured Outputs API** with **Pydantic validation v2** and a persistent cloud database layer, World Cradle completely eliminates LLM hallucinations, ensuring that complex creative assets map to predictable, database-ready JSON schemas.

---

## 🛠️ System Architecture & Tech Stack

- **Frontend Interface:** Streamlit (Multi-tab complex layouts, responsive data manipulation views)
- **Data Validation & Parsing Engine:** Pydantic v2 (Strict nested types, validation constraints)
- **AI Orchestration:** OpenAI API (GPT-4o / GPT-4o-mini execution via native JSON Schema parsing)
- **Persistence Layer:** PostgreSQL (Hosted via serverless cloud architecture on **Neon**)
- **Database Driver:** Psycopg2 (Utilizing connection pooling and relational query factories)

---

## 📐 Relational Data Schema

The platform guarantees relational linking across two primary entities, managing user historical variations through structural serialization:

* **Authors:** Unique developer profiles managed by strict email isolation rules.
* **Worlds:** Complete lore sets serialized as schema-validated `JSONB` blobs, providing ultra-fast querying capabilities.

```sql
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE worlds (
    world_id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL,
    world_name VARCHAR(255) NOT NULL,
    global_premise TEXT NOT NULL,
    tone VARCHAR(100) NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    world_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_author FOREIGN KEY(author_id) REFERENCES authors(author_id) ON DELETE CASCADE
);

CREATE INDEX idx_worlds_world_data ON worlds USING gin (world_data);
