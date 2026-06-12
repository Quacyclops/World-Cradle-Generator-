import streamlit as st
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

class Histories(BaseModel):
    event_name: str = Field(
        description="A few sentences about the event that occurred within the world as well as their impact on the world as a whole.")
    event_date: str = Field(
        description="The date the event occurred according to the date conventions within the world.")


class Religion(BaseModel):
    name: str = Field(description="The name of religion.")
    inception: str = Field(
        description="The inception of the religion as well as details about how the religion was created, the key figures involved in the creation of the religion and the reason the religion was created.")
    system: str = Field(
        description="A few sentences about the systems and beliefs held by the religion, what they believe in and how they worship.")
    order: str = Field(description="The hierarchy systems within the religion, eg, Chief priest, Prior, Weeper, etc.")


class Hierarchy(BaseModel):
    system: str = Field(
        description="The particular sort of government system practiced. eg, Monarchy, Democracy or any other unique system.")
    governance: str = Field(description="A few sentences about the particular governance practice that is adhered to.")


class Flora(BaseModel):
    name: str = Field(description="The name of flora.")
    properties: List[str] = Field(
        description="The list of properties describing the unique attributes and abilities of the flora, a few sentences per list expanding on each unique property")


class Fauna(BaseModel):
    name: str = Field(description="The name of fauna.")
    properties: List[str] = Field(
        description="The list of properties describing the unique attributes and abilities of the fauna, a few sentences per list expanding on each unique property")


class Region(BaseModel):
    name: str = Field(description="The name of region.")
    properties: str = Field(description="The detailed description of the unique or magical attributes of the region.")
    history: str = Field(
        description="The history of the region, its formation as well as some historical events that took place in it.")


class Factions(BaseModel):
    name: str = Field(description="The name of faction, tribes or peoples.")
    culture: str = Field(
        description="The unique cultures of the faction as well as their beliefs, practices and dominant religion which must be from the religions already established.")
    secret_weakness: str = Field(description="A few sentences about the secret weakness of the faction.")


class Weirdness(BaseModel):
    name: str = Field(description="The name of a completely unique object, place or attribute in the world.")
    effects: str = Field(
        description="A few sentences on the effect of the weirdness and how it has shaped the cultures and world as a whole.")


class LoreBible(BaseModel):
    world_name: str = Field(description="An evocative, original name for the fictional setting.")
    global_premise: str = Field(
        description="A comprehensive introduction establishing the core conflict, tone, and state of the world.")
    timeline: List[Histories] = Field(description="A list of 3-4 major historical milestones that defined this world or universe.")
    religions: List[Religion] = Field(
        description="The prominent faiths and spiritual orders observed by the inhabitants.")
    global_power_structure: Hierarchy = Field(
        description="The overarching system of governance or political landscape ruling the world or universe.")
    geography: List[Region] = Field(description="3-4 unique regions or territories that make up the world map.")
    botany: List[Flora] = Field(description="Notable plants and flora unique to this ecosystem.")
    zoology: List[Fauna] = Field(description="Notable creatures and fauna native to this world.")
    factions: List[Factions] = Field(
        description="The active groups, societies, or tribes competing or living within this world.")
    anomalies: List[Weirdness] = Field(
        description="1-2 highly distinct objects, phenomena, or local laws of physics that disrupt normalcy.")


load_dotenv()
#@st.cache_resource
def init_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


def get_or_create_author(name: str, email: str):
    conn = init_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO authors (name, email) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name RETURNING author_id;",
            (name, email)
        )
        conn.commit()
        return cur.fetchone()['author_id']


def save_world_to_db(author_id: int, world_name: str, premise: str, tone: str, model: str, pydantic_obj: LoreBible):
    conn = init_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO worlds (author_id, world_name, global_premise, tone, model_used, world_data)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING world_id;
            """,
            (author_id, world_name, premise, tone, model, pydantic_obj.model_dump_json())
        )
        conn.commit()


def fetch_author_worlds_history(author_id: int):
    conn = init_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT world_id, world_name, tone, created_at, world_data FROM worlds WHERE author_id = %s ORDER BY created_at DESC;",
            (author_id,)
        )
        return cur.fetchall()


st.set_page_config(page_title="Lore Bible Generator", page_icon="🌌", layout="wide")

st.title("🌌 World Cradle Lore Bible Generator")
st.caption(
    "Forge deep, structurally verified worldbuilding assets.")

with st.sidebar:
    st.header("👤 Author Account Profile")
    author_name = st.text_input("Author Profile Name", value="Tobi")
    author_email = st.text_input("Profile Email Access", value="tobi@example.com")

    if author_name and author_email:
        try:
            st.session_state.author_id = get_or_create_author(author_name, author_email)
            st.success(f"Connected as Author ID: {st.session_state.author_id}")
        except Exception as e:
            st.error(f"Database Unreachable: {e}")

    st.divider()
    st.header("🔑 Authentication & Tones")
    api_key = st.text_input("OpenAI API Key", type="password", help="Your key is processed locally and never stored.")

    selected_model = st.selectbox(
        "OpenAI Model Engine",
        ["gpt-4o-mini", "gpt-4o"],
        help="gpt-4o-mini is lightning fast and cost-efficient. gpt-4o offers good structural and narrative depth."
    )

    st.header("🎭 Setting Parameters")
    user_tone = st.selectbox(
        "World Tone",
        ["Grimdark", "High Fantasy", "Sci-Fantasy", "Urban Fantasy", "Cyberpunk", "Hard Sci-Fi", "Hopepunk",
         "Gothic Horror", "Steampunk Adventure"]
    )

    if "author_id" in st.session_state:
        st.divider()
        st.header("📚 Your Library Archive")
        previous_worlds = fetch_author_worlds_history(st.session_state.author_id)

        if previous_worlds:
            world_options = {f"{w['world_name']} ({w['tone']})": w for w in previous_worlds}
            selected_past_world = st.selectbox("Load Saved Timeline Vaults",
                                               ["-- Select an Archive --"] + list(world_options.keys()))

            if selected_past_world != "-- Select an Archive --":
                chosen_record = world_options[selected_past_world]
                st.session_state.lore_bible = LoreBible.model_validate(chosen_record['world_data'])

user_premise = st.text_area(
    "Core World Premise / Creative Spark:",
    height=150,
    placeholder="Describe the seed of your world here..."
)

naming_conventions = st.text_input(
    "Naming/Language Conventions:",
    placeholder="Describe your world's language and naming style here...E.g. Guttural with West African Inspirations."
)

generate_btn = st.button("Forge Lore Bible", type="primary", use_container_width=True)



def run_world_forge(key: str, premise: str, tone: str, naming_conventions: str, model_engine: str):
    """Executes the structured LLM generation sequence using arguments."""
    client = OpenAI(api_key=key)
    system_instruction = (
        f"You are an expert game designer, worldbuilder, and speculative fiction author. "
        f"Expand the user's creative spark into a granular, highly cohesive lore bible. "
        f"Strictly maintain a continuous {tone} aesthetic through every single field and nested object."
        f"Strictly follow the {naming_conventions} style in every name and title that is in every single field and nested object"
    )
    completion = client.beta.chat.completions.parse(
        model=model_engine,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Core World Premise: {premise}"}
        ],
        response_format=LoreBible,
    )
    return completion.choices[0].message.parsed


if generate_btn:
    if not api_key:
        st.error("🔒 Authentication missing! Please add your OpenAI API Key inside the left sidebar panel.")
    elif not user_premise:
        st.warning("✍️ Your world needs a spark! Please write a premise sentence before forging.")
    elif not naming_conventions:
        st.warning("Your world needs a language! Please write a naming convention sentence before forging.")
    elif "author_id" not in st.session_state:
        st.error("👤 Please verify your Author Profile configuration before processing generations.")
    else:
        with st.spinner(f"✨ Weaving your {user_tone} reality into existence... Please wait..."):
            try:
                generated_data = run_world_forge(key=api_key, premise=user_premise, tone=user_tone,
                                                 model_engine=selected_model, naming_conventions=naming_conventions)

                save_world_to_db(
                    author_id=st.session_state.author_id,
                    world_name=generated_data.world_name,
                    premise=user_premise,
                    tone=user_tone,
                    model=selected_model,
                    pydantic_obj=generated_data
                )

                st.session_state.lore_bible = generated_data
                st.success("🪐 Reality Matrix Formed and Saved to Database Vector Store!")
                st.rerun()

            except Exception as e:
                st.error(f"An internal execution error has surfaced: {e}")


if "lore_bible" in st.session_state:
    world = st.session_state.lore_bible

    st.divider()
    st.header(f"🪐 Codex Entry: {world.world_name}")
    st.markdown(f"*{world.global_premise}*")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏛 *History & Power*", "⛪ *Faiths & Factions*", "🗺 *Geography*", "🌿 *Eco-System*", "🔮 *Anomalies*"])

    with tab1:
        st.subheader("📋 Political Governance Model")
        st.write(f"**Government Classification:** {world.global_power_structure.system}")
        st.write(world.global_power_structure.governance)

        st.subheader("⏳ Historical Record Timeline")
        for event in world.timeline:
            with st.chat_message("user", avatar="⏱️"):
                st.write(f"**{event.event_date}** — *{event.event_name}*")

    with tab2:
        st.subheader("⛪ Organized World Faiths")
        for religion in world.religions:
            with st.expander(f"Faith: {religion.name}"):
                st.write(f"**Inception Chronicles:** {religion.inception}")
                st.write(f"**Belief Matrix:** {religion.system}")
                st.write(f"**Hierarchical Order:** `{religion.order}`")

        st.subheader("👥 Dynamic Societal Factions")
        for faction in world.factions:
            with st.expander(f"Faction Profile: {faction.name}"):
                st.write(f"**Cultural Practices:** {faction.culture}")
                st.write(f"**⚠️ Functional Defect / Vulnerability:** {faction.secret_weakness}")

    with tab3:
        st.subheader("🗺️ Registered Geographic Territories")
        for region in world.geography:
            with st.container(border=True):
                st.write(f"### 📍 Region: {region.name}")
                st.write(f"**Environmental Profiles:** {region.properties}")
                st.write(f"**Regional Local Lore:** {region.history}")

    with tab4:
        col_botany, col_zoology = st.columns(2)

        with col_botany:
            st.subheader("🌿 Local Specimen Flora")
            for plant in world.botany:
                st.markdown(f"**{plant.name}**")
                for prop in plant.properties:
                    st.write(f"- {prop}")

        with col_zoology:
            st.subheader("🐾 Native Adaptive Zoology")
            for beast in world.zoology:
                st.markdown(f"**{beast.name}**")
                for prop in beast.properties:
                    st.write(f"- {prop}")

    with tab5:
        st.subheader("⚠️ Reality Distortions & Paradoxes")
        for anomaly in world.anomalies:
            with st.chat_message("assistant", avatar="🌀"):
                st.write(f"### Object Variant: {anomaly.name}")
                st.write(f"**World Structural Alterations:** {anomaly.effects}")