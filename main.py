import os
import streamlit as st
import uuid
from agno.agent import Agent, RunResponse
from agno.models.groq import Groq
from agno.tools.eleven_labs import ElevenLabsTools
from agno.tools.firecrawl import FirecrawlTools
from agno.utils.audio import write_audio_to_file
from agno.utils.log import logger


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def generate_podcast(url: str):
    with st.spinner("Generating podcast for your URL..."):
        try:
            blog_to_podcast_agent = Agent(
                name="Blog to Podcast Agent",
                model=Groq(id="llama-3.1-8b-instant", max_tokens=6000),
                tools=[
                    ElevenLabsTools(
                        voice_id="21m00Tcm4TlvDq8ikWAM",
                        model_id="eleven_multilingual_v2",
                        target_directory="audio_generations",
                    ),
                    FirecrawlTools(),
                ],
                description="You are an agent that converts blog posts into audio podcasts.",
                instructions="""
                    When a user provides a URL:
                    1. Use FirecrawlTools to fetch the blog post content.
                    2. Create an engaging and informative podcast script covering all key points.
                    3. The script should be in a conversational tone and not exceed 2000 characters.
                    4. Use ElevenLabsTools to convert the entire script into a single audio file.
                """,
                markdown=True,
                debug_mode=True,
            )

            podcast: RunResponse = blog_to_podcast_agent.run(
                f"Generate a podcast for the blog post at {url}."
            )

            if podcast.audio and len(podcast.audio) > 0:
                saved_directory = "audio_generations"
                os.makedirs(saved_directory, exist_ok=True)
                file_name = f"{saved_directory}/podcast_{uuid.uuid4()}.mp3"
                write_audio_to_file(
                    audio=podcast.audio[0].base64_audio, filename=file_name
                )
                return file_name
            else:
                st.error("Failed to generate podcast audio. Please try again.")
                return None
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.error(f"An error occurred: {str(e)}")
            return None


st.set_page_config(page_title="Blog to Podcast", page_icon="🎙️", layout="wide")

local_css("assets/style.css")

st.title("Blog to Podcast")
st.markdown(
    """
    <div style="text-align: center; font-size: 1.2rem; color: #e0e0e0; margin-bottom: 2rem;">
        Transform any blog post into a captivating podcast with just one click. 
        <br>
        Paste the URL, and let our AI do the rest!
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("API KEYS")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password")
elevenlabs_api_key = st.sidebar.text_input("ElevenLabs API Key", type="password")
firecrawl_api_key = st.sidebar.text_input("Firecrawl API Key", type="password")

keys_provided = all([groq_api_key, elevenlabs_api_key, firecrawl_api_key])

url = st.text_input("Enter URL of BLOGPOST", "https://github.com/google-gemini/gemini-cli")

if st.button("Generate Podcast"):


    if not url.strip():
        st.warning("Please enter a URL to proceed.")

    if url=="https://github.com/google-gemini/gemini-cli":
        
        audio_bytes = open("audio_generations/sample_podcast.mp3", "rb").read()
        st.audio(audio_bytes, format="audio/mp3")
        st.download_button(
             label="Download Podcast",
             data=audio_bytes,
             file_name="Generated_Podcast.mp3",
             mime="audio/mp3",
        )

    if not keys_provided:
        st.warning("Please provide all API keys in the sidebar.")

    else:
        os.environ["GROQ_API_KEY"] = groq_api_key
        os.environ["ELEVEN_LABS_API_KEY"] = elevenlabs_api_key
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

        audio_file = generate_podcast(url)

        if audio_file:
            st.markdown('<div class="fadeInUp">', unsafe_allow_html=True)
            with st.expander("Listen to Your Podcast", expanded=True):
                st.success("Your Podcast is Ready!")
                audio_bytes = open(audio_file, "rb").read()
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label="Download Podcast",
                    data=audio_bytes,
                    file_name="Generated_Podcast.mp3",
                    mime="audio/mp3",
                )
            st.markdown("</div>", unsafe_allow_html=True)
