"""
Project Shikhara — Text-to-SQL Chatbot
- llama-3.1-70b-versatile for SQL generation (smarter, more accurate)
- llama-3.1-8b-instant for answer generation (fast)
- Retry logic if SQL fails or returns unexpected empty results
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client     = Groq(api_key=os.getenv("GROQ_API_KEY"))
SQL_MODEL  = "openai/gpt-oss-20b"    # fast model for SQL generation
ANS_MODEL  = "openai/gpt-oss-20b"    # fast model for answer formatting

# ── Database schema ───────────────────────────────────────────────────────────

SCHEMA = """
PostgreSQL database schema for Project Shikhara — a Hindu temple directory for Germany.

Tables:

1. temples (id, name, street, city, postal_code, location_latitude, location_longitude, note)
   - One row per temple

2. location (postal_code, state)
   - Maps German postal codes to their Bundesland (state)
   - e.g. 'Bayern', 'Berlin', 'Nordrhein-Westfalen', 'Hessen', 'Thüringen' etc.

3. temple_contact (id, temple_id, contact_type, value)
   - contact_type: 'phone', 'email', 'website', 'facebook', 'instagram'

4. temple_hours (id, temple_id, day, hours)
   - day: 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'
   - hours: string like '10:00–18:00', 'Closed', '08:00–13:00, 17:00–20:00'
   - Temples with NO hours data simply have no rows in this table
"""

SQL_PROMPT = """You are a PostgreSQL expert. Convert the user's question into a single SQL query.

STRICT RULES:
- Output ONLY the raw SQL query — no explanation, no markdown, no backticks, no comments
- Always include t.name and t.city in SELECT
- Use ILIKE for case-insensitive text matching on city/state names
- For open temples: exclude hours = 'Closed'
- LIMIT 30 rows maximum

EXAMPLES:

Q: temples open on Sundays in Berlin
SQL: SELECT DISTINCT t.name, t.city, h.hours AS sunday_hours FROM temples t JOIN temple_hours h ON t.id = h.temple_id WHERE t.city ILIKE 'Berlin' AND h.day = 'Sunday' AND h.hours != 'Closed' LIMIT 30

Q: temples open only on Sundays
SQL: SELECT t.name, t.city, h.hours AS sunday_hours FROM temples t JOIN temple_hours h ON t.id = h.temple_id WHERE h.day = 'Sunday' AND h.hours != 'Closed' AND t.id NOT IN (SELECT DISTINCT temple_id FROM temple_hours WHERE day != 'Sunday' AND hours != 'Closed') LIMIT 30

Q: temples open every day
SQL: SELECT t.name, t.city FROM temples t WHERE (SELECT COUNT(DISTINCT day) FROM temple_hours WHERE temple_id = t.id AND hours != 'Closed') = 7 LIMIT 30

Q: which state has the most temples
SQL: SELECT l.state, COUNT(*) AS temple_count FROM temples t JOIN location l ON t.postal_code = l.postal_code GROUP BY l.state ORDER BY temple_count DESC LIMIT 10

Q: temples with a website in Hamburg
SQL: SELECT t.name, t.city, c.value AS website FROM temples t JOIN temple_contact c ON t.id = c.temple_id WHERE t.city ILIKE 'Hamburg' AND c.contact_type = 'website' LIMIT 30

Q: temples in Bayern
SQL: SELECT t.name, t.city FROM temples t JOIN location l ON t.postal_code = l.postal_code WHERE l.state ILIKE 'Bayern' LIMIT 30

Q: how many temples are there in total
SQL: SELECT COUNT(*) AS total_temples FROM temples

Q: temples open on weekends
SQL: SELECT DISTINCT t.name, t.city FROM temples t JOIN temple_hours h ON t.id = h.temple_id WHERE h.day IN ('Saturday', 'Sunday') AND h.hours != 'Closed' LIMIT 30

Q: temples with evening hours
SQL: SELECT DISTINCT t.name, t.city, h.day, h.hours FROM temples t JOIN temple_hours h ON t.id = h.temple_id WHERE h.hours LIKE '%18:%' OR h.hours LIKE '%19:%' OR h.hours LIKE '%20:%' LIMIT 30

Schema:
{schema}

Question: {question}

SQL:"""

ANSWER_PROMPT = """You are Shikhara, a friendly assistant for a Hindu temple directory in Germany.
Present the database results below in a warm, natural, conversational way.

Rules:
- If results are present, list them clearly and helpfully
- If results are empty, say so naturally — e.g. "I couldn't find any temples matching that in our directory"
- Never question the accuracy of the results
- Never suggest the user check other sources
- Be concise — avoid long paragraphs
- Use a friendly tone, like a knowledgeable local guide
- Do NOT use markdown formatting like **bold** or *italic* — use plain text only
- Always complete every temple entry fully before moving to the next

Question: {question}

Results from our database:
{results}

Answer:"""


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )


def generate_sql(question: str, previous_sql: str = None, error: str = None) -> str:
    """Generate SQL — optionally with retry context if previous attempt failed."""
    prompt = SQL_PROMPT.format(schema=SCHEMA, question=question)

    if previous_sql and error:
        prompt += f"\n\nThe previous SQL failed with error: {error}\nPrevious SQL: {previous_sql}\nPlease fix it."

    response = client.chat.completions.create(
        model=SQL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=500,
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def execute_sql(sql: str) -> list:
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def generate_answer(question: str, results: list) -> str:
    results_str = json.dumps(results, ensure_ascii=False, indent=2) if results else "[]"
    response = client.chat.completions.create(
        model=ANS_MODEL,
        messages=[{"role": "user", "content": ANSWER_PROMPT.format(
            question=question, results=results_str
        )}],
        temperature=0.3,
        max_tokens=1000,
    )
    return response.choices[0].message.content.strip()


def ask(question: str) -> str:
    """Main entry: question → SQL → execute → natural answer. With retry on failure."""
    try:
        # Step 1: Generate SQL
        sql = generate_sql(question)
        print(f"Generated SQL:\n{sql}\n")

        # Step 2: Execute SQL
        try:
            results = execute_sql(sql)
            print(f"Results: {len(results)} rows\n")
        except Exception as sql_error:
            print(f"SQL failed: {sql_error} — retrying...\n")
            sql = generate_sql(question, previous_sql=sql, error=str(sql_error))
            print(f"Retry SQL:\n{sql}\n")
            results = execute_sql(sql)
            print(f"Retry results: {len(results)} rows\n")

        # Step 3: Generate answer
        return generate_answer(question, results)

    except Exception as e:
        return f"Sorry, something went wrong: {str(e)}"


def ask_stream(question: str):
    """Streaming version — yields status updates then answer tokens."""
    try:
        # Status 1: generating SQL
        yield "__STATUS__Searching the temple directory..."

        sql = generate_sql(question)
        print(f"Generated SQL:\n{sql}\n")

        # Status 2: running query
        yield "__STATUS__Running database query..."

        try:
            results = execute_sql(sql)
        except Exception as sql_error:
            yield "__STATUS__Refining query..."
            sql = generate_sql(question, previous_sql=sql, error=str(sql_error))
            results = execute_sql(sql)

        print(f"Results: {len(results)} rows\n")

        # Status 3: generating answer — then stream tokens
        yield "__STATUS__Preparing answer..."

        results_str = json.dumps(results, ensure_ascii=False, indent=2) if results else "[]"

        stream = client.chat.completions.create(
            model=ANS_MODEL,
            messages=[{"role": "user", "content": ANSWER_PROMPT.format(
                question=question, results=results_str
            )}],
            temperature=0.3,
            max_tokens=1000,
            stream=True,
        )

        yield "__ANSWER__"  # signal that answer tokens follow
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token

    except Exception as e:
        yield f"__STATUS__Error: {str(e)}"


if __name__ == "__main__":
    tests = [
        "Which temples are open only on Sundays?",
        "Which temples are present in Erfurt?",
        "Which state has the most temples?",
        "Which temples in Hamburg have a website?",
        "Are there any temples open on Sunday evenings?",
    ]
    for q in tests:
        print(f"Q: {q}")
        print(f"A: {ask(q)}")
        print("-" * 60)