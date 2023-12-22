import streamlit as st
from main_streamlit import *

#--------------------------------Web Page Designing------------------------------
hide_menu_style = """
    <style>
        MainMenu {visibility: hidden;}
        
        
         div[data-testid="stHorizontalBlock"]> div:nth-child(1)
        {  
            border : 2px solid #doe0db;
            border-radius:5px;
            text-align:center;
            color:black;
            background:dodgerblue;
            font-weight:bold;
            padding: 25px;
            
        }
        
        div[data-testid="stHorizontalBlock"]> div:nth-child(2)
        {   
            border : 2px solid #doe0db;
            background:dodgerblue;
            border-radius:5px;
            text-align:center;
            font-weight:bold;
            color:black;
            padding: 25px;
            
        }
    </style>
    """

main_title = """
            <div>
                <h1 style="color:black;
                text-align:center; font-size:35px;
                margin-top:-90px;">
                예인수조 안전시스템</h1>
            </div>
            """
#--------------------------------------------------------------------------------


#---------------------------Main Function for Execution--------------------------
def main():
    st.set_page_config(page_title='Dashboard', 
                       layout = 'wide', 
                       initial_sidebar_state = 'auto')
    
    st.markdown(hide_menu_style, 
                unsafe_allow_html=True)

    st.markdown(main_title,
                unsafe_allow_html=True)



    inference_msg = st.empty()
    st.sidebar.title("USER Configuration")
    

    input_source = st.sidebar.radio("Source",
                                         ('Video', 'WebCam'))

    conf_thres = st.sidebar.text_input("Class confidence threshold", 
                                       "0.25")

 
    save_output_video = st.sidebar.radio("Save output video?",
                                         ('Yes', 'No'))

    if save_output_video == 'Yes':
        nosave = False
        display_labels=False
   
    else:
        nosave = True
        display_labels = True 
           
    weights = "best.pt"
    device="cpu"

    # ------------------------- LOCAL VIDEO ------------------------
    if input_source == "Video":
        
        video = st.sidebar.file_uploader("Select input video", 
                                        type=["mp4", "avi", "mov"], 
                                        accept_multiple_files=False)

        if st.sidebar.button("Start Tracking"):
            
            stframe = st.empty()
            
            
            detect(weights=weights, 
                    source=f'video/{video.name}',  
                    stframe=stframe, 
                    conf_thres=float(conf_thres),
                    device="cpu",
                    nosave=nosave, 
                    )

            inference_msg.success("Inference Complete!")



    # ------------------------- LOCAL VIDEO ------------------------
    if input_source == "WebCam":
        
        if st.sidebar.button("Start Tracking"):
            
            stframe = st.empty()
            

            detect(weights=weights, 
                    source="0",  
                    stframe=stframe, 
                    conf_thres=float(conf_thres),
                    device="cpu",
                    nosave=nosave, 
                    display_labels=display_labels)

            inference_msg.success("Inference Complete!")

    # --------------------------------------------------------------       
    torch.cuda.empty_cache()
    # --------------------------------------------------------------



# --------------------MAIN FUNCTION CODE------------------------
if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
# ------------------------------------------------------------------
