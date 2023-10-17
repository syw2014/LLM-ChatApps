"""A website to create audio with minimax t2a api, features as bellow:
1. You can choose 4 different voice
2. With the given 4 voices and it's weight to combine a new voice.
"""
import streamlit as st
import requests
import yaml
import re
import datetime

st.set_page_config(
    page_title="Audio Combination App",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get Help": "https://ibb.co/G5y1H0j"},
)


# set page tile
st.title(" :blue[TimbreBlend: Combine  different timbres  Into one]")

st.markdown("""
**项目介绍**  
为提升声音音色效果，通过设置选择音色、设定其权重，将这些音色融合为一种音色进行输出；项目支持对声音的语速、音量、语调、音色和权重修改。   
:green[**Enjoy Yourself!**]
""")

st.divider()  # Draws a horizontal rule

# define placeholder for parameters for t2a api
st.sidebar.header("Parameters for T2A")
# sitebar
speed = st.sidebar.slider("speed", min_value=0.5, max_value=2.0, value=1.0)
vol = st.sidebar.slider("volume", min_value=0.1, max_value=10.0, value=1.0)
pitch = st.sidebar.slider("pitch", min_value=-12, max_value=12, value=0)
audio_sample_rate = st.sidebar.slider(
    "audio_sample_rate", min_value=16000, max_value=24000, value=24000)
bitrate = st.sidebar.selectbox(
    "bitrate",
    index=2,
    options=[32000, 64000, 128000])


# voice id list

# 暂时只支持系统音色(id):
# 青涩青年音色(male-qn-qingse)
# 精英青年音色(male-qn-jingying)
# 霸道青年音色(male-qn-badao)
# 青年大学生音色(male-qn-daxuesheng)
# 少女音色(female-shaonv)
# 御姐音色(female-yujie)
# 成熟女性音色(female-chengshu)
# 甜美女性音色(female-tianmei)
# 男性主持人(presenter_male)
# 女性主持人(presenter_female)
# 男性有声书1(audiobook_male_1)
# 男性有声书2(audiobook_male_2)
# 女性有声书1(audiobook_female_1)
# 女性有声书2(audiobook_female_2)

# 青涩青年音色-beta(male-qn-qingse-jingpin)
# 精英青年音色-beta(male-qn-jingying-jingpin)
# 霸道青年音色-beta(male-qn-badao-jingpin)
# 青年大学生音色-beta(male-qn-daxuesheng-jingpin)
# 少女音色-beta(female-shaonv-jingpin)
# 御姐音色-beta(female-yujie-jingpin)
# 成熟女性音色-beta(female-chengshu-jingpin)
# 甜美女性音色-beta(female-tianmei-jingpin)


voice_list = [
    "青涩青年音色",
    "精英青年音色",
    "霸道青年音色",
    "青年大学生音色",
    "少女音色",
    "御姐音色",
    "成熟女性音色",
    "甜美女性音色",
    "男性主持人",
    "女性主持人",
    "男性有声书1",
    "男性有声书2",
    "女性有声书1",
    "女性有声书2",
    "青涩青年音色-beta",
    "精英青年音色-beta",
    "霸道青年音色-beta",
    "青年大学生音色-beta",
    "少女音色-beta",
    "御姐音色-beta",
    "成熟女性音色-beta",
    "甜美女性音色-beta"
]

voice_dict = {
    "青涩青年音色": "male-qn-qingse",
    "精英青年音色": "male-qn-jingying",
    "霸道青年音色": "male-qn-badao",
    "青年大学生音色": "male-qn-daxuesheng",
    "少女音色": "female-shaonv",
    "御姐音色": "female-yujie",
    "成熟女性音色": "female-chengshu",
    "甜美女性音色": "female-tianmei",
    "男性主持人": "presenter_male",
    "女性主持人": "presenter_female",
    "男性有声书1": "audiobook_male_1",
    "男性有声书2": "audiobook_male_2",
    "女性有声书1": "audiobook_female_1",
    "女性有声书2": "audiobook_female_2",
    "青涩青年音色-beta": "male-qn-qingse-jingpin",
    "精英青年音色-beta": "male-qn-jingying-jingpin",
    "霸道青年音色-beta": "male-qn-badao-jingpin",
    "青年大学生音色-beta": "male-qn-daxuesheng-jingpin",
    "少女音色-beta": "female-shaonv-jingpin",
    "御姐音色-beta": "female-yujie-jingpin",
    "成熟女性音色-beta": "female-chengshu-jingpin",
    "甜美女性音色-beta": "female-tianmei-jingpin"
}


# voice 1
voice_id1 = st.sidebar.selectbox(
    "音色1",
    index=0,
    options=voice_list
)
voice_id1_w = st.sidebar.slider(
    "weight1",  min_value=1, max_value=100, value=10)

# voice 2
voice_id2 = st.sidebar.selectbox(
    "音色2",
    options=voice_list
)
voice_id2_w = st.sidebar.slider(
    "weight2",  min_value=1, max_value=100, value=10)

# voice 3
voice_id3 = st.sidebar.selectbox(
    "音色3",
    options=voice_list
)
voice_id3_w = st.sidebar.slider(
    "weight3",  min_value=1, max_value=100, value=10)

# voice 4
voice_id4 = st.sidebar.selectbox(
    "音色4",
    options=voice_list
)
voice_id4_w = st.sidebar.slider(
    "weight4",  min_value=1, max_value=100, value=10)


# define text input area
input_prompt = st.text_area(label="输入文本", height=100,
                            placeholder="输入文本")
prompt_button = st.button("合成", key="predict")


# group_id = "1684307302783428"
# api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJOYW1lIjoic2h1bndhbmdfZGV2IiwiU3ViamVjdElEIjoiMTY4NDMwNzMwMjAwNDg0MSIsIlBob25lIjoiTVRnNE1UYzROREEzTWpRPSIsIkdyb3VwSUQiOiIxNjg0MzA3MzAyNzgzNDI4IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoieXcuc2hpQHNodW53YW5nLmNvbSIsIkNyZWF0ZVRpbWUiOiIyMDIzLTA3LTEwIDExOjQ5OjUyIiwiaXNzIjoibWluaW1heCJ9.l9PLcwfH3Ungh1mqv-e2BH3jpUEmKxycMWM5DS199Qd6jaWWbz_hCVybjgj7MTZEYFdPtTrE2rXZy1W7IcF0v5S0rBETQSvxOYxsKRaZtYLgH9j9x7nchY3oHmBd6mUBPb1RVjWvcu3VnK3e7Xj2HRMZdzr_PRnDEsCLDDVlrMd5GAJG6pukuVMjUJ_-I48DQ9i-li_9n7BMex1LrlGCEDnwQ1avhyZ8lgtd5XaYop6cb2YRwBGMaVULe_JVdSA1DRLXrHkG5r8fgZ4J5Uv_XdIlud3G6Fg-8xrwbXJlblC-_MKZtH9BzB1RMqc3JGNWsC3DFj7mLuTvbNUKAhGbdA"

# url = f"https://api.minimax.chat/v1/t2a_pro?GroupId={group_id}"


@st.cache_data
def get_config():
    return yaml.safe_load(open("./config.yaml", "r"))


config = get_config()
url = config["Minimax"]["base"]["api_base"] + \
    str(config["Minimax"]["base"]["group_id"])
api_key = config["Minimax"]["base"]["api_key"]


headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

post_data = {
    # 如同时传入voice_id和timber_weights时，则会自动忽略voice_id，以timber_weights传递的参数为准
    "voice_id": voice_dict[voice_id1],
    "text": "",
    "model": "speech-01",
    "speed": speed,
    "vol": vol,
    "pitch": pitch,
    "audio_sample_rate": audio_sample_rate,
    "bitrate": int(bitrate),
    "timber_weights": [
        {
            "voice_id": voice_dict[voice_id1],
            "weight": voice_id1_w
        },
        {
            "voice_id": voice_dict[voice_id2],
            "weight": voice_id2_w
        },
        {
            "voice_id": voice_dict[voice_id3],
            "weight": voice_id3_w
        },
        {
            "voice_id": voice_dict[voice_id4],
            "weight": voice_id4_w
        }
    ]
}

st.markdown('''
    :red[**Voice Combination**]  
        **Voice1**: :orange[{} Weight: {}]  
        **Voice2**: :green[{} Weight: {}]  
        **Voice3**: :blue[{} weight: {}]  
        **Voice4**: :orange[{} Weight: {}]
    '''.format(
    voice_id1, voice_id1_w, voice_id2, voice_id2_w, voice_id3, voice_id3_w, voice_id4, voice_id4_w))

if prompt_button:
    # st.markdown('''
    # :red[**Voice Combination**]
    #     **Voice1**: :orange[{} Weight: {}]
    #     **Voice2**: :green[{} Weight: {}]
    #     **Voice3**: :blue[{} weight: {}]
    #     **Voice4**: :orange[{} Weight: {}]
    # '''.format(
    #     voice_id1, voice_id1_w, voice_id2, voice_id2_w, voice_id3, voice_id3_w, voice_id4, voice_id4_w))

    post_data["text"] = input_prompt

    # call api
    # TODO: may cost long time
    with st.spinner("Processing..."):
        response = requests.post(url, headers=headers, json=post_data)
        # print(response.status_code)

    if response.status_code == 200:
        json_res = response.json()
        # print("result->", json_res)
        audio_file_cdn = json_res["audio_file"]

        # extract filename of mp3
        pattern = r"([A-Za-z0-9-]+\.mp3)"

        match = re.search(pattern, audio_file_cdn)
        if match:
            name_str = match.group(1)
            audio_name = name_str.split("-")[-1]
            # audio_name = arrs[-1]
            # print("==", audio_name)
        else:
            audio_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".mp3"

        output_path = "./audios/" + audio_name

        # print("audio name->", audio_name)

        # Download mp3 files in local folder:./audios/
        try:
            req_content = requests.get(audio_file_cdn, allow_redirects=True)
            with open(output_path, 'wb') as f:
                f.write(req_content.content)
        except Exception as e:
            print("Download mp3 file error!")

        audio_fs = open(output_path, 'rb')
        audio_bytes = audio_fs.read()
        st.audio(audio_bytes, format='audio/wav')
        st.download_button(label="Download audio file",
                           data=audio_bytes, file_name=audio_name)
    else:
        st.write("Error: {}".format(response.status_code))
