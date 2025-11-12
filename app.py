import streamlit as st
from openai import OpenAI
import os
from google import genai

# --- CẤU HÌNH ---
# Nên dùng Streamlit Secrets để bảo mật API key khi deploy
# Trên máy local, bạn có thể tạo file .env hoặc điền thẳng vào đây
# Ví dụ: GOOGLE_API_KEY="YOUR_API_KEY"
try:
    # Cố gắng lấy API key từ Streamlit secrets (khi deploy)
    api_key = st.secrets["GOOGLE_API_KEY"]
    api_key_vip = st.secrets["GOOGLE_API_KEY_VIP"]
except (FileNotFoundError, KeyError):
    # Nếu không được, lấy từ biến môi trường (khi chạy local)
    # Bạn cần tạo file .env hoặc set biến môi trường thủ công
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    api_key_vip = os.getenv("GOOGLE_API_KEY_VIP")

# --- KHỞI TẠO MÔ HÌNH AI ---

client = OpenAI(
    api_key = api_key,
    base_url = 'https://generativelanguage.googleapis.com/v1beta/openai/'
)

# --- ĐỌC CƠ SỞ TRI THỨC (NẾU CÓ) ---
# Đọc file dữ liệu mẫu để cung cấp ngữ cảnh cho AI
try:
    with open("knowledge_base.txt", "r", encoding="utf-8") as f:
        knowledge_base = f.read()
except FileNotFoundError:
    knowledge_base = "Không có cơ sở tri thức nào được cung cấp."


# --- XÂY DỰNG GIAO DIỆN WEB ---
st.set_page_config(page_title="Trợ lý ảo cho Công chức xã", page_icon="🤖")
st.title("🤖 Trợ lý AI & Sáng tạo (công chức)")
st.caption("Made by VTC Edu")

# Tạo các tab
tab1, tab2 = st.tabs(["Trợ lý AI", "Tạo ảnh"])

# --- TAB 1: TRỢ LÝ AI ---
with tab1:
    st.header("Hỏi đáp về thủ tục hành chính")
    # Khởi tạo lịch sử chat trong session_state nếu chưa có
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Hiển thị các tin nhắn đã có từ lịch sử
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Nhận input từ người dùng. Logic được điều chỉnh để sửa lỗi hiển thị.
    if prompt := st.chat_input("Bạn cần tôi hỗ trợ về thủ tục hành chính nào?"):
        # Thêm tin nhắn của người dùng vào lịch sử
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Chuẩn bị prompt đầy đủ cho AI
        system_prompt = """Bạn là một trợ lý ảo chuyên nghiệp, am hiểu về các thủ tục hành chính của Việt Nam.
        Nhiệm vụ của bạn là trả lời các câu hỏi của công chức cấp xã một cách chính xác, rõ ràng và ngắn gọn.
        Sử dụng cơ sở tri thức dưới đây để trả lời (Ưu tiên viết đúng nội dung nguyên bản-không chỉnh sửa). 
        Nếu câu hỏi không có trong cơ sở tri thức, hãy trả lời dựa trên hiểu biết chung của bạn về luật pháp Việt Nam và nói rõ "Thông tin này mang tính tham khảo chung".
        """
        user_prompt = f"""
        --- CƠ SỞ TRI THỨC ---
        {knowledge_base}
        -----------------------
        Câu hỏi của người dùng: "{prompt}"
        """

        # Gọi API và nhận câu trả lời đầy đủ
        try:
            # Sử dụng stream=True để có hiệu ứng gõ chữ
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                responses = client.chat.completions.create(
                    model = 'gemini-2.5-flash',
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    stream=True)
                for chunk in responses:
                    full_response += (chunk.choices[0].delta.content or "")
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            
            # Thêm câu trả lời của AI vào lịch sử sau khi đã hiển thị xong
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            # Chạy lại script để đảm bảo ô chat input ở đúng vị trí sau khi gửi tin nhắn
            st.rerun()


        except Exception as e:
            st.error(f"Đã có lỗi xảy ra: {e}")
            full_response = "Xin lỗi, tôi không thể xử lý yêu cầu này."
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()

# --- TAB 2: TẠO ẢNH (SỬA LẠI TUÂN THỦ HƯỚNG DẪN OFFICIAL) ---
from PIL import Image # Cần import thư viện PIL

with tab2:
    st.header("Tạo ảnh & chỉnh sửa ảnh bằng AI")
    st.info("Mô tả hình ảnh bạn muốn tạo. Càng chi tiết, kết quả càng chính xác.")

    image_prompt = st.text_area("Nhập mô tả của bạn vào đây:", height=150)
    uploaded_ref = st.file_uploader("Upload ảnh tham khảo (tuỳ chọn)", type=["png","jpg","jpeg"])

    if st.button("Tạo ảnh"):
        if not image_prompt:
            st.warning("Vui lòng nhập mô tả cho ảnh bạn muốn tạo.")
        else:
            with st.spinner("AI đang vẽ, vừa gọi Gemini..."):
                try:
                    # KHỞI TẠO CLIENT GIỐNG HƯỚNG DẪN
                    # Sử dụng api_key_vip như code gốc của bạn
                    client = genai.Client(api_key=api_key_vip)

                    # CHUẨN BỊ CONTENTS THEO ĐÚNG ĐỊNH DẠNG YÊU CẦU
                    contents = [image_prompt]
                    if uploaded_ref is not None:
                        # THAY ĐỔI QUAN TRỌNG: Phải chuyển file upload thành đối tượng PIL.Image
                        # Đây là điểm mấu chốt gây lỗi trong code gốc của bạn.
                        ref_image = Image.open(uploaded_ref)
                        contents.append(ref_image)

                    # GỌI API VỚI ĐÚNG MODEL VÀ PHƯƠNG THỨC TRONG HƯỚNG DẪN
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-image", # Giữ nguyên tên model bạn đã cung cấp
                        contents=contents
                    )

                    st.subheader("Kết quả:")
                    
                    # XỬ LÝ KẾT QUẢ TRẢ VỀ ĐÚNG NHƯ HƯỚNG DẪN
                    # Cấu trúc response.parts là cấu trúc chuẩn
                    image_found = False
                    for part in response.parts:
                        # Dữ liệu ảnh nằm trong trường inline_data
                        if part.inline_data:
                            # Lấy dữ liệu bytes của ảnh
                            image_bytes = part.inline_data.data
                            
                            # Hiển thị ảnh lên giao diện Streamlit
                            st.image(image_bytes, caption="Ảnh do AI tạo ra.", width='content')
                            
                            # Thêm nút tải ảnh
                            st.download_button(
                                label="Tải ảnh xuống",
                                data=image_bytes,
                                file_name="generated_image.png",
                                mime="image/png"
                            )
                            image_found = True
                            break # Dừng lại sau khi hiển thị ảnh đầu tiên

                    if not image_found:
                        st.warning("AI không trả về hình ảnh. Vui lòng thử lại với mô tả khác.")
                        st.code(f"AI Response:\n{response.text}")


                except Exception as e:
                    st.error(f"Rất tiếc, đã có lỗi xảy ra khi tạo ảnh: {e}")
                    st.error("Gợi ý: Hãy đảm bảo API Key của bạn có quyền truy cập model 'gemini-2.5-flash-image' và ảnh bạn upload không bị lỗi.")