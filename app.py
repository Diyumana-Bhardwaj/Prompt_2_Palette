import streamlit as st
import pathlib
import requests
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

UNSPLASH_ACCESS_KEY = "tL################################"
PEXELS_API_KEY = "yN##########################################"
PIXABAY_API_KEY = "5#######################################"

# Function to load CSS from the 'assets' folder
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def fetch_image_urls(query, sources, num_images):
    urls = []
    total_sources = len(sources)
    
    # Determine how many images to fetch per source
    base_count = num_images // total_sources
    remainder = num_images % total_sources

    headers = {}
    source_image_counts = [base_count + (1 if i < remainder else 0) for i in range(total_sources)]

    for i, source in enumerate(sources):
        count = source_image_counts[i]
        if count == 0:
            continue

        headers = {}

        if source == 'unsplash':
            url = f"https://api.unsplash.com/search/photos?query={query}&per_page={count}"
            headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        elif source == 'pexels':
            url = f"https://api.pexels.com/v1/search?query={query}&per_page={count}"
            headers = {"Authorization": PEXELS_API_KEY}
        elif source == 'pixabay':
            count=max(count,3)
            url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=photo&per_page={count}"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if source == 'unsplash':
                source_urls = [item['urls']['regular'] for item in data.get('results', [])]
            elif source == 'pexels':
                source_urls = [item['src']['medium'] for item in data.get('photos', [])]
            elif source == 'pixabay':
                source_urls = [item['largeImageURL'] for item in data.get('hits', [])]
            else:
                source_urls = []

            urls.extend(source_urls[:count])

        except Exception as e:
            print(f"❌ Error fetching from {source}: {str(e)}")

    return urls


def fetch_image_from_url(image_url):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert("RGB")
    return image

def extract_dominant_colors(image, num_colors=5):
    # Resize for faster processing
    image = image.resize((200, 200))
    data = np.array(image).reshape(-1, 3)

    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(data)

    colors = kmeans.cluster_centers_.astype(int)
    hex_colors = ['#%02x%02x%02x' % tuple(color) for color in colors]
    return hex_colors

def plot_colors(hex_colors, k, url):
    plt.figure(figsize=(8, 2))
    for i, hex_color in enumerate(hex_colors):
        plt.fill_between([i, i+1], 0, 1, color=hex_color)
    plt.xticks([])
    plt.yticks([])
    plt.title(f"Color Palette No.{k+1}")
    st.pyplot(plt)
    cols = st.columns(len(hex_colors))
    for i, hex_color in enumerate(hex_colors):
        with cols[i]:
            st.markdown(f"""<div class="color">{hex_color}</div>""", unsafe_allow_html=True)
            # st.code(str(hex_colors), language="python")
    if url !="None":
        st.markdown(f"[🖼️ View Image Source]({url})", unsafe_allow_html=True)

def main():
    css_path = pathlib.Path("assets/styles.css")
    if css_path.exists():
        load_css(css_path)
    else:
        st.warning("🎨 Custom CSS not found. Running with default style.")



    st.title("Prompt-2-Palette Dashboard")
    st.subheader("From text prompts to perfect palettes — instantly, intelligently, beautifully.", divider="rainbow")


    prompt = st.text_input("Enter your design prompt (e.g., sunset beach, luxury, forest camp):")
    source = st.multiselect(
    "Select platforms to take inspiration from",
    ["UNSPLASH","PIXABAY","PEXELS"],
    default=["UNSPLASH"]
    )
    sources = [s.lower() for s in source]
    st.write("---OR---")
    use_upload = st.toggle("Upload Image to extract palette")
    if use_upload:
        uploaded_image=st.file_uploader("Choose an image",type=['jpg','jpeg','png'])
    k = st.slider("🌈 Number of Colors", min_value=3
    , max_value=8, value=5)
    if use_upload:
            no_palette = 1  # Just 1 palette from uploaded image
            st.slider("🌈 Number of palettes (disabled for uploads)", min_value=1, max_value=7, value=1, disabled=True)
    else:
        no_palette = st.slider("🌈 Number of palettes", min_value=1, max_value=7, value=3)

    submit=st.button("Generate",key="button")

    if submit:
        if use_upload:
            try:
                image = Image.open(uploaded_image).convert("RGB")
                st.image(image,caption="Uploaded Image",use_container_width=True)
                hex_colors = extract_dominant_colors(image, k)
                plot_colors(hex_colors, 0, "None")
            except:
                # st.warning("Please upload image which is applicable for given conditions!!!!")
                st.markdown('<div class="custom-warning">⚠️ Please upload image which is applicable for given conditions!</div>', unsafe_allow_html=True)
        else:
            if not prompt.strip():
                st.markdown('<div class="custom-warning">⚠️ Please enter a valid prompt!</div>', unsafe_allow_html=True)
            elif not sources:
                st.markdown('<div class="custom-warning">⚠️ Please select at least one source!</div>', unsafe_allow_html=True)
            elif no_palette<len(sources):
                st.markdown('<div class="custom-warning">⚠️ Number of palettes is less than the selected sources. Adjusting sources to match palette count.</div>', unsafe_allow_html=True)
            else:
                image_urls = fetch_image_urls(prompt, sources, no_palette)
                image_urls = image_urls[:no_palette]  # Limit to first K

                if not image_urls:
                    st.markdown('<div class="custom-warning">⚠️No images found for the given prompt and source!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="custom-info">ℹ️ Fetching Suitable Images...</div>', unsafe_allow_html=True)
                    st.markdown('<div class="custom-success">✅ Extracted Color Palette Successfully!</div>', unsafe_allow_html=True)
                    for url in image_urls:
                        image = fetch_image_from_url(url)
                        hex_colors = extract_dominant_colors(image, k)
                        plot_colors(hex_colors,image_urls.index(url),url)
                        


if __name__=="__main__":
    main()
