import streamlit as st
import pandas as pd
import json
from typing import Optional, Dict, List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import requests
from datetime import datetime
import groq
from config import env_vars

class DataProcessor:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.primary_column: Optional[str] = None
        self.google_creds = None

    def _load_google_credentials(self) -> Optional[Credentials]:
        """Loads Google Sheets credentials from a JSON file."""
        try:
            # Pass the file path as a string, not the file object
            creds = Credentials.from_service_account_file('sustained-node-441417-b2-873b87007eca.json')

            # Define the required API scopes
            scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            
            # Ensure the credentials include the necessary scopes
            creds = creds.with_scopes(scopes)
            return creds
        
        except FileNotFoundError:
            st.error("Google credentials file not found. Please ensure the file exists and is in the correct location.")
            return None
        except json.JSONDecodeError:
            st.error("Invalid JSON format in Google Sheets credentials file.")
            return None
        except Exception as e:
            st.error(f"Error loading Google Sheets credentials: {str(e)}")
            return None

    def load_google_sheet(self, sheet_id: str) -> bool:
        """Loads a Google Sheet into a pandas DataFrame."""
        try:
            # Load credentials only when needed
            self.google_creds = self._load_google_credentials()
            if not self.google_creds:
                return False
                
            # Use the credentials to authorize the Google Sheets API client
            service = build('sheets', 'v4', credentials=self.google_creds)
            sheet = service.spreadsheets()
            
            # Fetch the values from the sheet (adjust range as needed)
            result = sheet.values().get(spreadsheetId=sheet_id, range='A1:ZZ1000').execute()
            values = result.get('values', [])
            
            if not values:
                st.error("No data found in Google Sheet.")
                return False
            
            # Convert to pandas DataFrame
            self.df = pd.DataFrame(values[1:], columns=values[0])
            
            # Clean up data (strip leading/trailing whitespaces and fill NaN values)
            self.df = self.df.fillna('')
            self.df = self.df.astype(str)
            for column in self.df.columns:
                self.df[column] = self.df[column].str.strip()
            
            return True
        except Exception as e:
            st.error(f"Error loading Google Sheet: {str(e)}")
            return False
    def load_csv(self, file) -> bool:
        """Load CSV file into a DataFrame"""
        try:
            self.df = pd.read_csv(file)
            self.df = self.df.fillna('')
            self.df = self.df.astype(str)
            for column in self.df.columns:
                self.df[column] = self.df[column].str.strip()
            return True
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return False
        
    def get_columns(self) -> List[str]:
        """Get list of column names in the DataFrame"""
        return list(self.df.columns) if self.df is not None else []

    def get_value(self, row: pd.Series, column: str) -> str:
        """Safely get a value from a row, handling missing values"""
        try:
            value = row[column]
            if pd.isna(value) or value is None:
                return ""
            return str(value).strip()
        except Exception:
            return ""

class WebSearcher:
    def __init__(self):
        self.api_key = env_vars['SERPAPI_KEY']
    
    def search(self, query: str) -> List[Dict]:
        """Perform a web search using SerpApi"""
        if not query or not query.strip():
            st.warning("Empty search query")
            return []
            
        try:
            params = {
                "api_key": self.api_key,
                "q": query.strip(),
                "num": 5  # Number of results to return
            }
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            results = response.json().get('organic_results', [])
            return results
        except requests.exceptions.RequestException as e:
            st.error(f"Search error: {str(e)}")
            return []
        except Exception as e:
            st.error(f"Unexpected error during search: {str(e)}")
            return []

class LLMProcessor:
    def __init__(self):
        self.client = groq.Groq(api_key=env_vars['GROQ_API_KEY'])
    
    def process_results(self, search_results: List[Dict], prompt: str) -> str:
        """Process search results using LLM"""
        if not search_results:
            return "No search results found"
            
        try:
            context = "\n".join([
                f"Title: {result.get('title', '')}\n"
                f"Snippet: {result.get('snippet', '')}\n"
                for result in search_results
            ])
            
            system_prompt = """Extract the requested information from the provided search results. 
            If the information cannot be found, respond with 'Not found'.
            Be concise and only return the requested information."""
            
            completion = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nPrompt: {prompt}"}
                ],
                temperature=0.3
            )
            
            return completion.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"LLM processing error: {str(e)}")
            return "Error processing results"
    

def process_entity(entity: str, query_template: str, searcher: WebSearcher, llm_processor: LLMProcessor) -> Dict:
    """Process a single entity and return results"""
    try:
        entity_str = str(entity).strip()
        if not entity_str:
            return {"Entity": entity, "Extracted Information": "Empty entity value"}
        
        query = query_template.replace("{entity}", entity_str)
        search_results = searcher.search(query)
        extracted_info = llm_processor.process_results(search_results, query)
        
        return {"Entity": entity_str, "Extracted Information": extracted_info}
    except Exception as e:
        st.error(f"Error processing entity '{entity}': {str(e)}")
        return {"Entity": str(entity), "Extracted Information": "Error during processing"}

def main():
    st.title("AI Data Enrichment Agent")
    
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()
    if 'results' not in st.session_state:
        st.session_state.results = None
    
    # Data Input Section
    st.header("1. Data Input")
    input_type = st.radio("Select input type:", ["CSV Upload", "Google Sheets"])
    
    if input_type == "CSV Upload":
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        if uploaded_file:
            if st.session_state.data_processor.load_csv(uploaded_file):
                st.success("CSV loaded successfully!")
    else:
        sheet_id = st.text_input("Enter Google Sheet ID")
        if st.button("Load Sheet") and sheet_id:
            if st.session_state.data_processor.load_google_sheet(sheet_id):
                st.success("Google Sheet loaded successfully!")
    
    # Column Selection
    if st.session_state.data_processor.df is not None:
        columns = st.session_state.data_processor.get_columns()
        if not columns:
            st.error("No columns found in the data")
            return
            
        primary_column = st.selectbox("Select primary column:", columns)
        st.session_state.data_processor.primary_column = primary_column
        
        st.dataframe(st.session_state.data_processor.df.head())
        
        # Query Configuration
        st.header("2. Query Configuration")
        query_template = st.text_area(
            "Enter search query template:",
            "Get me the email address of {entity}"
        )
        
        if st.button("Process Data"):
            if not query_template or "{entity}" not in query_template:
                st.error("Please enter a valid query template containing {entity}")
                return
                
            searcher = WebSearcher()
            llm_processor = LLMProcessor()
            
            results = []
            progress_bar = st.progress(0)
            total_rows = len(st.session_state.data_processor.df)
            
            # Process each row
            for idx, row in st.session_state.data_processor.df.iterrows():
                entity = st.session_state.data_processor.get_value(row, primary_column)
                result = process_entity(entity, query_template, searcher, llm_processor)
                results.append(result)
                
                # Update progress
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
            
            # Create results DataFrame
            st.session_state.results = pd.DataFrame(results)
            
            # Display Results
            st.header("3. Results")
            st.dataframe(st.session_state.results)
            
            # Download Options
            if not st.session_state.results.empty:
                st.download_button(
                    label="Download CSV",
                    data=st.session_state.results.to_csv(index=False),
                    file_name=f"enriched_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()
