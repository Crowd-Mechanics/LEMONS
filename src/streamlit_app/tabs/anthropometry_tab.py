"""Visualise the anthropometric ANSURII dataset."""

# Copyright  2025  Institute of Light and Matter, CNRS UMR 5306, University Claude Bernard Lyon 1
# Contributors: Oscar DUFOUR, Maxime STAPELLE, Alexandre NICOLAS

# This software is a computer program designed to generate a realistic crowd from anthropometric data and
# simulate the mechanical interactions that occur within it and with obstacles.

# This software is governed by the CeCILL-B license under French law and abiding by the rules of distribution
# of free software.  You can  use, modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL "http://www.cecill.info".

# As a counterpart to the access to the source code and  rights to copy, modify and redistribute granted by
# the license, users are provided only with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited liability.

# In this respect, the user's attention is drawn to the risks associated with loading,  using,  modifying
# and/or developing or reproducing the software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also therefore means  that it is reserved
# for developers  and  experienced professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their requirements in conditions enabling
# the security of their systems and/or data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.

# The fact that you are presently reading this means that you have had knowledge of the CeCILL-B license and that
# you accept its terms.

from pathlib import Path

import streamlit as st

import configuration.utils.functions as fun
from streamlit_app.plot import plot


def run_tab_anthropometry() -> None:
    """
    Provide an interactive interface for visualizing and analyzing anthropometric data from the ANSUR II database.

    Attributes
    ----------
    Main Page:
        - Visualization of the selected attribute's distribution using Plotly.
        - Statistical summaries (mean and standard deviation) for males and females displayed on the right side of the screen.
        - Link to the ANSUR II database website.
    """
    # Load the dataset from a pickle file
    path_file = Path(__file__).parent.parent.parent.parent / "data" / "pkl"
    df = fun.load_pickle(str(path_file / "ANSUREIIPublic.pkl"))

    # Define default attributes to display
    default_attributes = [
        "Sex",
        "Height [cm]",
        "Chest depth [cm]",
        "Bideltoid breadth [cm]",
        "Weight [kg]",
    ]

    # Sidebar: allow users to select attributes dynamically
    st.sidebar.title("Adjust parameters")
    selected_attribute = st.sidebar.selectbox(
        "Select an attribute",
        options=default_attributes,
    )

    # Display title on the main page
    st.subheader("Visualisation of the ANSURII database")
    # Define the URL of the database website
    database_url = "https://ph.health.mil/topics/workplacehealth/ergo/Pages/Anthropometric-Database.aspx"
    # Use st.markdown to create a clickable link
    st.markdown(f"Visit the [database website]({database_url})")

    # Main page content
    col1, col2 = st.columns([1.4, 1])  # Adjust proportions as needed
    with col1:
        fig = plot.display_distribution(df, selected_attribute.lower())
        st.plotly_chart(fig, width="stretch")
        # # Sidebar: Button to download the graph in PDF format # Requites kaleido package that causes issues on some OS
        # selected_attribute_name = selected_attribute.replace(" ", "_")
    with col2:
        # display the mean and standard deviation of the selected attribute for man and woman
        if selected_attribute.lower() not in ["sex", "weight [kg]"]:
            df_male = df[df["sex"] == "male"]
            df_female = df[df["sex"] == "female"]
            st.write("**Male**")
            st.write(f"Mean = {df_male[selected_attribute.lower()].mean():.2f} cm ")
            st.write(f"Standard deviation = {df_male[selected_attribute.lower()].std():.2f} cm ")
            st.write("**Female**")
            st.write(f"Mean = {df_female[selected_attribute.lower()].mean():.2f} cm ")
            st.write(f"Standard deviation = {df_female[selected_attribute.lower()].std():.2f} cm ")
        elif selected_attribute.lower() == "weight [kg]":
            df_male = df[df["sex"] == "male"]
            df_female = df[df["sex"] == "female"]
            st.write("**Male**")
            st.write(f"Mean = {df_male[selected_attribute.lower()].mean():.2f} kg ")
            st.write(f"Standard deviation = {df_male[selected_attribute.lower()].std():.2f} kg ")
            st.write("**Female**")
            st.write(f"Mean = {df_female[selected_attribute.lower()].mean():.2f} kg ")
            st.write(f"Standard deviation = {df_female[selected_attribute.lower()].std():.2f} kg ")

    # Download section in the sidebar
    st.sidebar.title("Download")

    # # Add a download button for the plot # Requites kaleido package that causes issues on some OS
    # st.sidebar.download_button(
    #     label="Download plot as PDF",
    #     data=fig.to_image(format="pdf"),
    #     file_name=f"{selected_attribute_name}_distribution.pdf",
    #     mime="application/pdf",
    #     width="stretch",
    # )

    # Add a selectbox for choosing the dataset to download
    path_file = Path(__file__).parent.parent.parent.parent / "data" / "csv"

    df = fun.load_csv(path_file / "ANSURIIFEMALEPublic.csv")
    download_filename = "anthropometric_data_ANSURIIFEMALEPublic.csv"
    # Prepare the data for download
    data_to_download = df.to_csv(index=False).encode("utf-8")
    # Add the download button for the dataset
    st.sidebar.download_button(
        label="Download female dataset as CSV",
        data=data_to_download,
        file_name=download_filename,
        mime="text/csv",
        width="stretch",
    )

    df = fun.load_csv(path_file / "ANSURIIMALEPublic.csv")
    download_filename = "anthropometric_data_ANSURIIMALEPublic.csv"
    # Prepare the data for download
    data_to_download = df.to_csv(index=False).encode("utf-8")
    # Add the download button for the dataset
    st.sidebar.download_button(
        label="Download male dataset as CSV",
        data=data_to_download,
        file_name=download_filename,
        mime="text/csv",
        width="stretch",
    )
